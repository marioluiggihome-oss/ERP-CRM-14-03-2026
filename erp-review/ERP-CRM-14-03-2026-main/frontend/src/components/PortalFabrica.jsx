import React, { useState, useEffect, useCallback } from 'react';
import { 
  Factory, Package, Clock, CheckCircle, Truck, AlertTriangle, 
  Plus, Search, Filter, Calendar, FileText, Upload, Download,
  ChevronDown, ChevronRight, Edit3, Trash2, Eye, Printer,
  BarChart3, TrendingUp, Box, Scissors, RefreshCw, X,
  FolderOpen, Check, Play, Pause, Square, History, Building2
} from 'lucide-react';
import { fabricaAPI, projectsAPI } from '../services/api';
import ProductionDashboard from './ProductionDashboard';
import OrderHistory from './OrderHistory';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Colores de estado
const STATUS_CONFIG = {
  draft: { label: 'Borrador', color: 'bg-gray-100 text-gray-700', icon: FileText },
  confirmed: { label: 'Confirmada', color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  in_production: { label: 'En Producción', color: 'bg-amber-100 text-amber-700', icon: Factory },
  ready: { label: 'Fabricada', color: 'bg-emerald-100 text-emerald-700', icon: Package },
  delivered: { label: 'Entregada', color: 'bg-green-100 text-green-700', icon: Truck },
  cancelled: { label: 'Cancelada', color: 'bg-red-100 text-red-700', icon: X }
};

const PRIORITY_CONFIG = {
  low: { label: 'Baja', color: 'bg-slate-100 text-slate-600' },
  normal: { label: 'Normal', color: 'bg-blue-50 text-blue-600' },
  high: { label: 'Alta', color: 'bg-orange-100 text-orange-700' },
  urgent: { label: 'Urgente', color: 'bg-red-100 text-red-700' }
};

// Clasificar muebles por categoría
const classifyFurniture = (productCode, productName) => {
  const code = (productCode || '').toUpperCase();
  const name = (productName || '').toUpperCase();
  
  // Altos: A*
  if (code.startsWith('A') || name.includes('ALTO')) return 'altos';
  // Bajos: B*
  if (code.startsWith('B') || name.includes('BAJO')) return 'bajos';
  // Columnas: CH*, CO*
  if (code.startsWith('CH') || name.includes('COLUMNA')) return 'columnas';
  // Semicolumnas: SCH*, SC*
  if (code.startsWith('SCH') || code.startsWith('SC') || name.includes('SEMICOLUMNA')) return 'semicolumnas';
  // Sobremódulos: SM*, SO*
  if (code.startsWith('SM') || code.startsWith('SO') || name.includes('SOBREMODULO') || name.includes('SOBREMÓDULO')) return 'sobremodulos';
  // Especiales: resto
  return 'especiales';
};

// Componente de barra de progreso de fabricación
const FabricationProgressBar = ({ items = [] }) => {
  const total = items.length;
  if (total === 0) return null;
  
  const completed = items.filter(i => i.fabricationStatus === 'completed').length;
  const inProgress = items.filter(i => i.fabricationStatus === 'in_progress').length;
  const pending = total - completed - inProgress;
  
  const completedPercent = (completed / total) * 100;
  const inProgressPercent = (inProgress / total) * 100;
  
  // Determinar color principal
  let statusColor = 'bg-red-500'; // Sin empezar
  let statusText = 'Sin empezar';
  if (completedPercent === 100) {
    statusColor = 'bg-emerald-500';
    statusText = 'Fabricado';
  } else if (completedPercent > 0 || inProgressPercent > 0) {
    statusColor = 'bg-blue-500';
    statusText = 'En proceso';
  }
  
  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs mb-1">
        <span className={`font-bold ${completedPercent === 100 ? 'text-emerald-600' : completedPercent > 0 ? 'text-blue-600' : 'text-red-500'}`}>
          {statusText}
        </span>
        <span className="text-gray-500">
          {completed}/{total} muebles
        </span>
      </div>
      <div className="h-3 bg-red-200 rounded-full overflow-hidden flex">
        {/* Parte fabricada (verde) */}
        <div 
          className="h-full bg-emerald-500 transition-all duration-500"
          style={{ width: `${completedPercent}%` }}
        />
        {/* Parte en proceso (azul) */}
        <div 
          className="h-full bg-blue-500 transition-all duration-500"
          style={{ width: `${inProgressPercent}%` }}
        />
        {/* El resto queda rojo (del fondo) */}
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>{pending} pendientes</span>
        <span>{inProgress} en proceso</span>
        <span>{completed} fabricados</span>
      </div>
    </div>
  );
};

// Resumen por categoría de muebles
const CategorySummary = ({ items = [] }) => {
  const summary = { altos: 0, bajos: 0, columnas: 0, semicolumnas: 0, sobremodulos: 0, especiales: 0 };
  
  items.forEach(item => {
    const category = classifyFurniture(item.productCode, item.productName);
    summary[category] += item.quantity || 1;
  });
  
  const categories = [
    { key: 'altos', label: 'Altos', color: 'bg-sky-100 text-sky-700 border-sky-300' },
    { key: 'bajos', label: 'Bajos', color: 'bg-amber-100 text-amber-700 border-amber-300' },
    { key: 'columnas', label: 'Columnas', color: 'bg-violet-100 text-violet-700 border-violet-300' },
    { key: 'semicolumnas', label: 'Semicol.', color: 'bg-teal-100 text-teal-700 border-teal-300' },
    { key: 'sobremodulos', label: 'Sobremód.', color: 'bg-indigo-100 text-indigo-700 border-indigo-300' },
    { key: 'especiales', label: 'Especiales', color: 'bg-rose-100 text-rose-700 border-rose-300' }
  ];
  
  // Solo mostrar categorías con items
  const activeCategories = categories.filter(cat => summary[cat.key] > 0);
  
  return (
    <div className="flex flex-wrap gap-2 my-3">
      {activeCategories.length === 0 ? (
        <span className="text-gray-400 text-sm">Sin muebles</span>
      ) : (
        activeCategories.map(cat => (
          <div key={cat.key} className={`${cat.color} border rounded-lg px-3 py-1 text-center`}>
            <span className="text-lg font-black">{summary[cat.key]}</span>
            <span className="text-[10px] font-bold uppercase ml-1">{cat.label}</span>
          </div>
        ))
      )}
    </div>
  );
};

const PortalFabrica = ({ currentUser }) => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [filters, setFilters] = useState({ status: '', priority: '', search: '' });
  const [expandedOrders, setExpandedOrders] = useState({});
  const [activeTab, setActiveTab] = useState('orders'); // 'orders', 'dashboard', 'history'
  const [factories, setFactories] = useState([]);
  
  // Modals
  const [showNewOrderModal, setShowNewOrderModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showImportFromProjectsModal, setShowImportFromProjectsModal] = useState(false);
  const [showDeliveryDateModal, setShowDeliveryDateModal] = useState(null);
  const [showDespieceModal, setShowDespieceModal] = useState(null);
  const [despieceData, setDespieceData] = useState(null);
  const [loadingDespiece, setLoadingDespiece] = useState(false);

  // Cargar fábricas
  useEffect(() => {
    const loadFactories = async () => {
      try {
        const response = await fetch(`${API_URL}/api/fabrica/factories`);
        if (response.ok) {
          const data = await response.json();
          setFactories(data.filter(f => f.isActive !== false));
        }
      } catch (err) {
        console.error('Error loading factories:', err);
      }
    };
    loadFactories();
  }, []);

  // Filtrar órdenes por fábrica del usuario si tiene una asignada
  const filteredOrdersByFactory = React.useMemo(() => {
    if (currentUser?.factoryId) {
      return orders.filter(o => o.factoryId === currentUser.factoryId || !o.factoryId);
    }
    // Gerentes, Directores Comerciales y Responsables de Delegación pueden ver todas
    if (currentUser?.isGerente || currentUser?.isDirectorComercial || currentUser?.isResponsableDelegacion || currentUser?.isAdmin) {
      return orders;
    }
    // Por defecto mostrar todas si tiene acceso a fábrica
    return orders;
  }, [orders, currentUser]);

  // Cargar datos
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ordersRes, statsRes] = await Promise.all([
        fabricaAPI.getOrders(filters),
        fabricaAPI.getDashboardStats()
      ]);
      setOrders(ordersRes.orders || []);
      setStats(statsRes);
    } catch (error) {
      console.error('Error loading factory data:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Cambiar estado de orden
  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await fabricaAPI.updateOrderStatus(orderId, newStatus);
      loadData();
    } catch (error) {
      alert('Error al cambiar estado: ' + error.message);
    }
  };

  // Marcar item como fabricado
  const handleMarkItemFabricated = async (orderId, itemId, newStatus) => {
    try {
      // Actualizar la orden con el nuevo estado del item
      const order = orders.find(o => o.id === orderId);
      if (!order) return;
      
      const updatedItems = order.items.map(item => {
        if (item.id === itemId) {
          return { ...item, fabricationStatus: newStatus };
        }
        return item;
      });
      
      await fabricaAPI.updateOrder(orderId, { items: updatedItems });
      loadData();
    } catch (error) {
      alert('Error al actualizar estado: ' + error.message);
    }
  };

  // Establecer fecha de entrega
  const handleSetDeliveryDate = async (orderId, date, notes) => {
    try {
      await fabricaAPI.setDeliveryDate(orderId, date, notes);
      setShowDeliveryDateModal(null);
      loadData();
    } catch (error) {
      alert('Error al establecer fecha: ' + error.message);
    }
  };

  // Eliminar orden
  const handleDeleteOrder = async (orderId) => {
    if (!window.confirm('¿Eliminar esta orden de fabricación?')) return;
    try {
      await fabricaAPI.deleteOrder(orderId);
      loadData();
    } catch (error) {
      alert('Error al eliminar: ' + error.message);
    }
  };

  // Cambiar fábrica de una orden existente
  const handleFactoryChange = async (orderId, factoryValue) => {
    try {
      let updateData = {};
      
      if (factoryValue === 'external') {
        const factoryName = prompt('Nombre de la fábrica externa:');
        if (!factoryName) return;
        updateData = {
          factoryType: 'external',
          factoryId: null,
          factoryName: factoryName
        };
      } else if (factoryValue) {
        const factory = factories.find(f => f.id === factoryValue);
        updateData = {
          factoryType: 'internal',
          factoryId: factoryValue,
          factoryName: factory?.name || ''
        };
      } else {
        updateData = {
          factoryType: 'internal',
          factoryId: null,
          factoryName: ''
        };
      }
      
      await fabricaAPI.updateOrder(orderId, updateData);
      loadData();
    } catch (error) {
      alert('Error al cambiar fábrica: ' + error.message);
    }
  };

  // Ver despiece de una orden
  const handleViewDespiece = async (orderId) => {
    setLoadingDespiece(true);
    setShowDespieceModal(orderId);
    try {
      const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}/despiece`);
      if (response.ok) {
        const data = await response.json();
        setDespieceData(data);
      } else {
        const error = await response.json();
        alert('Error: ' + (error.detail || 'No se pudo cargar el despiece'));
        setShowDespieceModal(null);
      }
    } catch (error) {
      alert('Error al cargar despiece: ' + error.message);
      setShowDespieceModal(null);
    } finally {
      setLoadingDespiece(false);
    }
  };

  // Descargar informe de producción PDF
  const handleDownloadProductionReport = async (orderId) => {
    try {
      const response = await fetch(`${API_URL}/api/fabrica/reports/production/${orderId}`);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error descargando informe' }));
        throw new Error(error.detail || 'Error al descargar informe');
      }
      
      // Obtener el blob y descargarlo
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Buscar el número de orden para el nombre del archivo
      const order = orders.find(o => o.id === orderId);
      const filename = `Informe_Produccion_${order?.orderNumber || orderId}.pdf`;
      a.download = filename;
      
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      alert('Error al descargar informe: ' + error.message);
    }
  };

  // Toggle expandir orden
  const toggleExpand = (orderId) => {
    setExpandedOrders(prev => ({ ...prev, [orderId]: !prev[orderId] }));
  };

  // Renderizar tarjeta de estadísticas
  const StatCard = ({ title, value, icon: Icon, color = 'indigo', subtitle }) => (
    <div className={`bg-white rounded-2xl p-5 border border-${color}-100 shadow-sm`}>
      <div className="flex items-center justify-between mb-2">
        <p className={`text-xs font-bold uppercase tracking-widest text-${color}-400`}>{title}</p>
        <div className={`p-2 bg-${color}-100 rounded-xl`}>
          <Icon size={18} className={`text-${color}-600`} />
        </div>
      </div>
      <p className={`text-3xl font-black text-${color}-900`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );

  // Vista de lista de órdenes
  const OrderListView = () => (
    <div className="space-y-3">
      {filteredOrdersByFactory.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-dashed border-indigo-200">
          <Factory size={48} className="mx-auto text-indigo-200 mb-4" />
          <p className="text-indigo-400 font-bold">No hay órdenes de fabricación</p>
          <p className="text-indigo-300 text-sm mt-1">Crea una nueva orden o importa desde un presupuesto</p>
          <div className="flex gap-3 justify-center mt-4">
            <button
              onClick={() => setShowNewOrderModal(true)}
              className="bg-indigo-600 text-white px-6 py-2 rounded-xl font-bold text-sm hover:bg-indigo-700 transition-colors"
            >
              Crear Orden
            </button>
            <button
              onClick={() => setShowImportFromProjectsModal(true)}
              className="bg-emerald-600 text-white px-6 py-2 rounded-xl font-bold text-sm hover:bg-emerald-700 transition-colors"
            >
              Importar de Pedido
            </button>
          </div>
        </div>
      ) : (
        filteredOrdersByFactory.map(order => {
          const statusConfig = STATUS_CONFIG[order.status] || STATUS_CONFIG.draft;
          const priorityConfig = PRIORITY_CONFIG[order.priority] || PRIORITY_CONFIG.normal;
          const StatusIcon = statusConfig.icon;
          const isExpanded = expandedOrders[order.id];
          const assignedFactory = factories.find(f => f.id === order.factoryId);

          return (
            <div key={order.id} className="bg-white rounded-2xl border border-indigo-100 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
              {/* Header */}
              <div 
                className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-indigo-50/50"
                onClick={() => toggleExpand(order.id)}
              >
                <div className="flex items-center gap-4">
                  <button className="p-1">
                    {isExpanded ? <ChevronDown size={20} className="text-indigo-400" /> : <ChevronRight size={20} className="text-indigo-400" />}
                  </button>
                  <div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-black text-indigo-900">{order.orderNumber}</span>
                      {order.manufacturingNumber && (
                        <span className="px-2 py-0.5 rounded bg-indigo-950 text-white text-xs font-bold" title="Número de Fabricación">
                          Nº FAB: {order.manufacturingNumber}
                        </span>
                      )}
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${statusConfig.color}`}>
                        <StatusIcon size={12} className="inline mr-1" />
                        {statusConfig.label}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${priorityConfig.color}`}>
                        {priorityConfig.label}
                      </span>
                      {assignedFactory && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 flex items-center gap-1">
                          <Building2 size={10} />
                          {assignedFactory.code}
                        </span>
                      )}
                      {order.factoryType === 'external' && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-700 flex items-center gap-1" title="Fábrica Externa">
                          <Truck size={10} />
                          EXT: {order.factoryName || 'Subcontratada'}
                        </span>
                      )}
                      {!assignedFactory && order.factoryType !== 'external' && !order.factoryId && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 flex items-center gap-1" title="Fábrica Propia">
                          <Factory size={10} />
                          Propia
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-indigo-600 mt-0.5">{order.customerName || 'Sin cliente'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  {/* Mini barra de progreso */}
                  <div className="w-32">
                    <FabricationProgressBar items={order.items || []} />
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="text-xs text-indigo-400 font-bold uppercase">Muebles</p>
                      <p className="font-black text-indigo-900">{order.items?.length || 0}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-indigo-400 font-bold uppercase">Entrega</p>
                      <p className={`font-bold ${order.estimatedDeliveryDate ? 'text-emerald-600' : 'text-gray-400'}`}>
                        {order.estimatedDeliveryDate 
                          ? new Date(order.estimatedDeliveryDate).toLocaleDateString('es-ES') 
                          : 'Sin fecha'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-6 pb-4 border-t border-indigo-50">
                  {/* Resumen por categoría */}
                  <CategorySummary items={order.items || []} />
                  
                  {/* Items con estado de fabricación */}
                  {order.items && order.items.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-black text-indigo-400 uppercase tracking-widest mb-2">
                        Muebles en la orden - Haz clic para marcar como fabricado
                      </p>
                      <div className="bg-indigo-50 rounded-xl overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-indigo-100">
                            <tr className="text-xs text-indigo-700 uppercase">
                              <th className="px-4 py-2 text-left">Código</th>
                              <th className="px-4 py-2 text-left">Descripción</th>
                              <th className="px-4 py-2 text-center">Dimensiones</th>
                              <th className="px-4 py-2 text-center">Tipo</th>
                              <th className="px-4 py-2 text-center">Cant.</th>
                              <th className="px-4 py-2 text-center">Estado Fabricación</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-indigo-100">
                            {order.items.map((item, idx) => {
                              const category = classifyFurniture(item.productCode, item.productName);
                              const fabStatus = item.fabricationStatus || 'pending';
                              
                              const categoryColors = {
                                altos: 'bg-sky-100 text-sky-700',
                                bajos: 'bg-amber-100 text-amber-700',
                                columnas: 'bg-violet-100 text-violet-700',
                                especiales: 'bg-rose-100 text-rose-700'
                              };
                              
                              const fabStatusConfig = {
                                pending: { label: 'Pendiente', color: 'bg-red-500', icon: Square },
                                in_progress: { label: 'En proceso', color: 'bg-blue-500', icon: Play },
                                completed: { label: 'Fabricado', color: 'bg-emerald-500', icon: Check }
                              };
                              
                              const statusConf = fabStatusConfig[fabStatus] || fabStatusConfig.pending;
                              const StatusFabIcon = statusConf.icon;
                              
                              return (
                                <tr key={item.id || idx} className="bg-white">
                                  <td className="px-4 py-2 font-bold text-indigo-900">{item.productCode}</td>
                                  <td className="px-4 py-2 text-indigo-600">{item.productName}</td>
                                  <td className="px-4 py-2 text-center text-xs">{item.width}×{item.height}×{item.depth} cm</td>
                                  <td className="px-4 py-2 text-center">
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${categoryColors[category]}`}>
                                      {category.charAt(0).toUpperCase() + category.slice(1)}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2 text-center font-bold text-orange-600">{item.quantity}</td>
                                  <td className="px-4 py-2">
                                    <div className="flex items-center justify-center gap-1">
                                      {/* Botones para cambiar estado de fabricación */}
                                      <button
                                        onClick={(e) => { e.stopPropagation(); handleMarkItemFabricated(order.id, item.id, 'pending'); }}
                                        className={`p-1.5 rounded-lg transition-all ${fabStatus === 'pending' ? 'bg-red-500 text-white' : 'bg-red-100 text-red-500 hover:bg-red-200'}`}
                                        title="Pendiente"
                                      >
                                        <Square size={14} />
                                      </button>
                                      <button
                                        onClick={(e) => { e.stopPropagation(); handleMarkItemFabricated(order.id, item.id, 'in_progress'); }}
                                        className={`p-1.5 rounded-lg transition-all ${fabStatus === 'in_progress' ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-500 hover:bg-blue-200'}`}
                                        title="En proceso"
                                      >
                                        <Play size={14} />
                                      </button>
                                      <button
                                        onClick={(e) => { e.stopPropagation(); handleMarkItemFabricated(order.id, item.id, 'completed'); }}
                                        className={`p-1.5 rounded-lg transition-all ${fabStatus === 'completed' ? 'bg-emerald-500 text-white' : 'bg-emerald-100 text-emerald-500 hover:bg-emerald-200'}`}
                                        title="Fabricado"
                                      >
                                        <Check size={14} />
                                      </button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {/* Cambiar Estado */}
                    <select
                      value={order.status}
                      onChange={(e) => handleStatusChange(order.id, e.target.value)}
                      className="px-3 py-1.5 border border-indigo-200 rounded-lg text-sm font-bold text-indigo-700 bg-white"
                      data-testid={`order-status-select-${order.id}`}
                    >
                      <option value="draft">Borrador</option>
                      <option value="confirmed">Confirmada</option>
                      <option value="in_production">En Producción</option>
                      <option value="ready">Fabricada</option>
                      <option value="delivered">Entregada</option>
                      <option value="cancelled">Cancelada</option>
                    </select>

                    {/* Cambiar Fábrica */}
                    <select
                      value={order.factoryType === 'external' ? 'external' : (order.factoryId || '')}
                      onChange={(e) => handleFactoryChange(order.id, e.target.value)}
                      className="px-3 py-1.5 border border-orange-200 rounded-lg text-sm font-bold text-orange-700 bg-orange-50"
                      data-testid={`order-factory-select-${order.id}`}
                    >
                      <option value="">🏠 Mi Fábrica</option>
                      {factories.map(f => (
                        <option key={f.id} value={f.id}>🏭 {f.name} ({f.code})</option>
                      ))}
                      <option value="external">📦 Externa/Subcontratada</option>
                    </select>

                    <button
                      onClick={() => setShowDeliveryDateModal(order)}
                      className="px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-lg text-sm font-bold hover:bg-emerald-200 flex items-center gap-1"
                      data-testid={`set-delivery-date-${order.id}`}
                    >
                      <Calendar size={14} />
                      Fecha Entrega
                    </button>

                    <button
                      onClick={() => handleViewDespiece(order.id)}
                      className="px-3 py-1.5 bg-orange-100 text-orange-700 rounded-lg text-sm font-bold hover:bg-orange-200 flex items-center gap-1"
                      data-testid={`view-despiece-${order.id}`}
                    >
                      <Scissors size={14} />
                      Ver Despiece
                    </button>

                    <button
                      onClick={() => handleDownloadProductionReport(order.id)}
                      className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm font-bold hover:bg-blue-200 flex items-center gap-1"
                      data-testid={`download-report-${order.id}`}
                      title="Descargar Informe de Producción PDF con logo y despiece"
                    >
                      <FileText size={14} />
                      Informe PDF
                    </button>

                    <button
                      onClick={() => handleDeleteOrder(order.id)}
                      className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-bold hover:bg-red-200 flex items-center gap-1"
                      data-testid={`delete-order-${order.id}`}
                    >
                      <Trash2 size={14} />
                      Eliminar
                    </button>
                  </div>

                  {/* Notes */}
                  {(order.internalNotes || order.productionNotes) && (
                    <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <p className="text-xs font-bold text-amber-700 uppercase mb-1">Notas</p>
                      <p className="text-sm text-amber-800">{order.internalNotes || order.productionNotes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );

  // Modal para nueva orden
  const NewOrderModal = () => {
    const [formData, setFormData] = useState({
      customerName: '',
      customerCode: '',
      contactPhone: '',
      deliveryAddress: '',
      priority: 'normal',
      items: [],
      internalNotes: '',
      factoryType: 'internal',
      factoryId: '',
      factoryName: ''
    });
    const [newItem, setNewItem] = useState({
      productCode: '',
      productName: '',
      quantity: 1,
      width: 60,
      height: 70,
      depth: 58
    });

    const handleAddItem = () => {
      if (!newItem.productCode) return;
      setFormData(prev => ({
        ...prev,
        items: [...prev.items, { ...newItem, id: `temp-${Date.now()}`, fabricationStatus: 'pending' }]
      }));
      setNewItem({ productCode: '', productName: '', quantity: 1, width: 60, height: 70, depth: 58 });
    };

    const handleRemoveItem = (index) => {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    };

    const handleFactoryChange = (factoryId) => {
      if (factoryId === 'external') {
        setFormData(prev => ({ ...prev, factoryType: 'external', factoryId: '', factoryName: '' }));
      } else if (factoryId) {
        const factory = factories.find(f => f.id === factoryId);
        setFormData(prev => ({ 
          ...prev, 
          factoryType: 'internal', 
          factoryId: factoryId, 
          factoryName: factory?.name || '' 
        }));
      } else {
        setFormData(prev => ({ ...prev, factoryType: 'internal', factoryId: '', factoryName: '' }));
      }
    };

    const handleSubmit = async () => {
      if (formData.items.length === 0) {
        alert('Añade al menos un mueble a la orden');
        return;
      }
      try {
        await fabricaAPI.createOrder(formData, currentUser?.id, currentUser?.clientName);
        setShowNewOrderModal(false);
        loadData();
      } catch (error) {
        alert('Error al crear orden: ' + error.message);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/70 z-[9999] flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Factory size={24} />
              <h2 className="font-black text-lg">Nueva Orden de Fabricación</h2>
            </div>
            <button onClick={() => setShowNewOrderModal(false)} className="p-2 hover:bg-white/10 rounded-xl">
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6 space-y-6">
            {/* Datos del cliente */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-indigo-400 uppercase">Cliente *</label>
                <input
                  type="text"
                  value={formData.customerName}
                  onChange={(e) => setFormData(prev => ({ ...prev, customerName: e.target.value }))}
                  className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"
                  placeholder="Nombre del cliente"
                  data-testid="new-order-customer-name"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-indigo-400 uppercase">Código Cliente</label>
                <input
                  type="text"
                  value={formData.customerCode}
                  onChange={(e) => setFormData(prev => ({ ...prev, customerCode: e.target.value }))}
                  className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"
                  placeholder="CLI-001"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-indigo-400 uppercase">Teléfono</label>
                <input
                  type="text"
                  value={formData.contactPhone}
                  onChange={(e) => setFormData(prev => ({ ...prev, contactPhone: e.target.value }))}
                  className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"
                  placeholder="600 123 456"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-indigo-400 uppercase">Prioridad</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"
                  data-testid="new-order-priority"
                >
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                  <option value="urgent">Urgente</option>
                </select>
              </div>
            </div>

            {/* Selector de Fábrica */}
            <div className="bg-gradient-to-r from-indigo-50 to-violet-50 rounded-xl p-4 border border-indigo-200">
              <label className="text-xs font-bold text-indigo-600 uppercase flex items-center gap-2 mb-2">
                <Building2 size={14} />
                Fábrica de Producción
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <select
                    value={formData.factoryType === 'external' ? 'external' : formData.factoryId}
                    onChange={(e) => handleFactoryChange(e.target.value)}
                    className="w-full px-4 py-2 border border-indigo-300 rounded-xl focus:border-indigo-500 outline-none bg-white"
                    data-testid="new-order-factory-select"
                  >
                    <option value="">Mi Fábrica (Interna)</option>
                    {factories.map(f => (
                      <option key={f.id} value={f.id}>{f.name} ({f.code})</option>
                    ))}
                    <option value="external">🏭 Fábrica Externa / Subcontratada</option>
                  </select>
                </div>
                {formData.factoryType === 'external' && (
                  <div>
                    <input
                      type="text"
                      value={formData.factoryName}
                      onChange={(e) => setFormData(prev => ({ ...prev, factoryName: e.target.value }))}
                      className="w-full px-4 py-2 border border-indigo-300 rounded-xl focus:border-indigo-500 outline-none"
                      placeholder="Nombre de la fábrica externa"
                      data-testid="new-order-factory-external-name"
                    />
                  </div>
                )}
              </div>
              <p className="text-xs text-indigo-500 mt-2">
                {formData.factoryType === 'external' 
                  ? '📦 Esta orden será producida por una fábrica subcontratada'
                  : formData.factoryId 
                    ? `✓ Producción asignada a ${factories.find(f => f.id === formData.factoryId)?.name || 'fábrica seleccionada'}`
                    : '🏠 Producción en tu propia fábrica'}
              </p>
            </div>

            <div>
              <label className="text-xs font-bold text-indigo-400 uppercase">Dirección de Entrega</label>
              <input
                type="text"
                value={formData.deliveryAddress}
                onChange={(e) => setFormData(prev => ({ ...prev, deliveryAddress: e.target.value }))}
                className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none"
                placeholder="Calle, número, ciudad..."
              />
            </div>

            {/* Añadir muebles */}
            <div>
              <p className="text-xs font-bold text-indigo-400 uppercase mb-2">Muebles a Fabricar</p>
              <div className="bg-indigo-50 rounded-xl p-4">
                <div className="grid grid-cols-6 gap-2 mb-2">
                  <input
                    type="text"
                    value={newItem.productCode}
                    onChange={(e) => setNewItem(prev => ({ ...prev, productCode: e.target.value }))}
                    className="col-span-1 px-3 py-2 border border-indigo-200 rounded-lg text-sm"
                    placeholder="Código"
                  />
                  <input
                    type="text"
                    value={newItem.productName}
                    onChange={(e) => setNewItem(prev => ({ ...prev, productName: e.target.value }))}
                    className="col-span-2 px-3 py-2 border border-indigo-200 rounded-lg text-sm"
                    placeholder="Descripción"
                  />
                  <input
                    type="number"
                    value={newItem.width}
                    onChange={(e) => setNewItem(prev => ({ ...prev, width: parseFloat(e.target.value) || 0 }))}
                    className="px-3 py-2 border border-indigo-200 rounded-lg text-sm text-center"
                    placeholder="Ancho"
                  />
                  <input
                    type="number"
                    value={newItem.height}
                    onChange={(e) => setNewItem(prev => ({ ...prev, height: parseFloat(e.target.value) || 0 }))}
                    className="px-3 py-2 border border-indigo-200 rounded-lg text-sm text-center"
                    placeholder="Alto"
                  />
                  <input
                    type="number"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                    className="px-3 py-2 border border-indigo-200 rounded-lg text-sm text-center"
                    placeholder="Cant."
                  />
                </div>
                <button
                  onClick={handleAddItem}
                  className="w-full py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700"
                  data-testid="add-item-btn"
                >
                  + Añadir Mueble
                </button>
              </div>

              {/* Lista de muebles añadidos con resumen */}
              {formData.items.length > 0 && (
                <>
                  <CategorySummary items={formData.items} />
                  <div className="mt-2 space-y-2">
                    {formData.items.map((item, idx) => (
                      <div key={item.id || idx} className="flex items-center justify-between bg-white border border-indigo-100 rounded-lg px-4 py-2">
                        <div className="flex items-center gap-4">
                          <span className="font-bold text-indigo-900">{item.productCode}</span>
                          <span className="text-indigo-600">{item.productName}</span>
                          <span className="text-xs text-gray-500">{item.width}×{item.height}×{item.depth} cm</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-orange-600">×{item.quantity}</span>
                          <button onClick={() => handleRemoveItem(idx)} className="text-red-500 hover:text-red-700">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Notas */}
            <div>
              <label className="text-xs font-bold text-indigo-400 uppercase">Notas Internas</label>
              <textarea
                value={formData.internalNotes}
                onChange={(e) => setFormData(prev => ({ ...prev, internalNotes: e.target.value }))}
                className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl focus:border-indigo-500 outline-none h-20"
                placeholder="Notas para producción..."
              />
            </div>
          </div>

          <div className="border-t border-indigo-100 px-6 py-4 flex justify-end gap-3">
            <button
              onClick={() => setShowNewOrderModal(false)}
              className="px-6 py-2 border border-indigo-200 rounded-xl font-bold text-indigo-600 hover:bg-indigo-50"
            >
              Cancelar
            </button>
            <button
              onClick={handleSubmit}
              className="px-6 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700"
              data-testid="submit-new-order"
            >
              Crear Orden
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Modal para fecha de entrega
  const DeliveryDateModal = () => {
    const [date, setDate] = useState('');
    const [notes, setNotes] = useState('');

    if (!showDeliveryDateModal) return null;

    return (
      <div className="fixed inset-0 bg-black/70 z-[9999] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl w-full max-w-md p-6">
          <h3 className="font-black text-lg text-indigo-900 mb-4">Establecer Fecha de Entrega</h3>
          <p className="text-sm text-indigo-600 mb-4">Orden: {showDeliveryDateModal.orderNumber}</p>
          
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-indigo-400 uppercase">Fecha Estimada</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl"
                data-testid="delivery-date-input"
              />
            </div>
            <div>
              <label className="text-xs font-bold text-indigo-400 uppercase">Notas</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full mt-1 px-4 py-2 border border-indigo-200 rounded-xl h-20"
                placeholder="Notas sobre la entrega..."
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={() => setShowDeliveryDateModal(null)}
              className="px-4 py-2 border border-indigo-200 rounded-xl font-bold text-indigo-600"
            >
              Cancelar
            </button>
            <button
              onClick={() => handleSetDeliveryDate(showDeliveryDateModal.id, date, notes)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-xl font-bold"
              data-testid="save-delivery-date"
            >
              Guardar Fecha
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Modal para importar desde proyectos/pedidos existentes
  const ImportFromProjectsModal = () => {
    const [projects, setProjects] = useState([]);
    const [loadingProjects, setLoadingProjects] = useState(true);
    const [selectedProject, setSelectedProject] = useState(null);
    const [importing, setImporting] = useState(false);

    useEffect(() => {
      const loadProjects = async () => {
        try {
          const result = await projectsAPI.list();
          // Filtrar solo proyectos con items montada
          const projectsWithItems = (result.projects || []).filter(p => 
            p.itemsMontada && p.itemsMontada.length > 0
          );
          setProjects(projectsWithItems);
        } catch (error) {
          console.error('Error loading projects:', error);
        } finally {
          setLoadingProjects(false);
        }
      };
      if (showImportFromProjectsModal) {
        loadProjects();
      }
    }, [showImportFromProjectsModal]);

    const handleImportProject = async (project) => {
      setImporting(true);
      try {
        await fabricaAPI.importFromBudget(project.id, currentUser?.id, currentUser?.clientName);
        alert(`Orden creada desde presupuesto: ${project.budgetNumber || project.id}`);
        setShowImportFromProjectsModal(false);
        loadData();
      } catch (error) {
        alert('Error al importar: ' + error.message);
      } finally {
        setImporting(false);
      }
    };

    if (!showImportFromProjectsModal) return null;

    return (
      <div className="fixed inset-0 bg-black/70 z-[9999] flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="bg-emerald-700 text-white px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <FolderOpen size={24} />
              <h2 className="font-black text-lg">Importar desde Pedidos Existentes</h2>
            </div>
            <button onClick={() => setShowImportFromProjectsModal(false)} className="p-2 hover:bg-white/10 rounded-xl">
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6">
            {loadingProjects ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw size={32} className="animate-spin text-emerald-600" />
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-12">
                <FolderOpen size={48} className="mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500 font-bold">No hay pedidos con muebles</p>
                <p className="text-gray-400 text-sm">Crea un presupuesto primero desde la sección Presupuestos</p>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-500 mb-4">
                  Selecciona un presupuesto para crear una orden de fabricación con sus muebles:
                </p>
                {projects.map(project => (
                  <div 
                    key={project.id}
                    className={`border rounded-xl p-4 cursor-pointer transition-all ${
                      selectedProject?.id === project.id 
                        ? 'border-emerald-500 bg-emerald-50' 
                        : 'border-gray-200 hover:border-emerald-300 hover:bg-emerald-50/50'
                    }`}
                    onClick={() => setSelectedProject(project)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-black text-lg text-gray-900">
                            {project.budgetNumber || `P-${project.id.slice(-6)}`}
                          </span>
                          <span className="text-sm text-emerald-600 font-bold">
                            {project.itemsMontada?.length || 0} muebles
                          </span>
                        </div>
                        <p className="text-gray-600">{project.customerName || 'Sin cliente'}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Creado: {new Date(project.createdAt).toLocaleDateString('es-ES')}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <CategorySummary items={project.itemsMontada || []} />
                        <button
                          onClick={(e) => { e.stopPropagation(); handleImportProject(project); }}
                          disabled={importing}
                          className="px-4 py-2 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 disabled:opacity-50"
                        >
                          {importing ? 'Importando...' : 'Importar'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="border-t border-gray-100 px-6 py-4 flex justify-end">
            <button
              onClick={() => setShowImportFromProjectsModal(false)}
              className="px-6 py-2 border border-gray-200 rounded-xl font-bold text-gray-600 hover:bg-gray-50"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Modal para importar PDF
  const ImportModal = () => {
    const [file, setFile] = useState(null);
    const [importing, setImporting] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [creatingOrder, setCreatingOrder] = useState(false);

    const handleFileChange = (e) => {
      const selectedFile = e.target.files[0];
      if (selectedFile && selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setAnalysisResult(null);
      } else {
        alert('Por favor selecciona un archivo PDF');
      }
    };

    const handleAnalyze = async () => {
      if (!file) return;
      setImporting(true);
      setAnalysisResult(null);
      try {
        const reader = new FileReader();
        reader.onload = async (e) => {
          const base64 = e.target.result.split(',')[1];
          const result = await fabricaAPI.importPDF(base64, file.name);
          setAnalysisResult(result);
        };
        reader.readAsDataURL(file);
      } catch (error) {
        alert('Error al analizar: ' + error.message);
      } finally {
        setImporting(false);
      }
    };

    const handleCreateOrder = async () => {
      if (!analysisResult?.detectedItems?.length) return;
      setCreatingOrder(true);
      try {
        const orderData = {
          customerName: 'Cliente PDF',
          customerCode: '',
          priority: 'normal',
          items: analysisResult.detectedItems.map(item => ({
            productCode: item.productCode,
            productName: item.productName,
            quantity: item.quantity || 1,
            width: item.width || 60,
            height: item.height || 70,
            depth: item.depth || 58,
            fabricationStatus: 'pending'
          })),
          internalNotes: `Importado desde PDF: ${file?.name}`
        };
        
        await fabricaAPI.createOrder(orderData, currentUser?.id, currentUser?.clientName);
        alert('Orden de fabricación creada correctamente');
        setShowImportModal(false);
        setAnalysisResult(null);
        setFile(null);
        loadData();
      } catch (error) {
        alert('Error al crear orden: ' + error.message);
      } finally {
        setCreatingOrder(false);
      }
    };

    if (!showImportModal) return null;

    return (
      <div className="fixed inset-0 bg-black/70 z-[9999] flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Upload size={24} />
              <h2 className="font-black text-lg">Importar Presupuesto PDF con IA</h2>
            </div>
            <button onClick={() => { setShowImportModal(false); setAnalysisResult(null); setFile(null); }} className="p-2 hover:bg-white/10 rounded-xl">
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6">
            {/* Selección de archivo */}
            <div className="border-2 border-dashed border-indigo-200 rounded-xl p-6 text-center mb-6">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="pdf-upload"
              />
              <label htmlFor="pdf-upload" className="cursor-pointer">
                <Upload size={40} className="mx-auto text-indigo-300 mb-2" />
                <p className="text-indigo-600 font-bold">Arrastra un PDF o haz clic para seleccionar</p>
                <p className="text-sm text-indigo-400 mt-1">La IA analizará el documento y detectará los muebles</p>
              </label>
              {file && (
                <p className="mt-3 text-emerald-600 font-bold flex items-center justify-center gap-2">
                  <FileText size={18} />
                  {file.name}
                </p>
              )}
            </div>

            {/* Botón analizar */}
            {file && !analysisResult && (
              <button
                onClick={handleAnalyze}
                disabled={importing}
                className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2 mb-6"
                data-testid="analyze-pdf-btn"
              >
                {importing ? (
                  <>
                    <RefreshCw size={18} className="animate-spin" />
                    Analizando con IA...
                  </>
                ) : (
                  <>
                    <Scissors size={18} />
                    Analizar PDF con IA
                  </>
                )}
              </button>
            )}

            {/* Resultados del análisis */}
            {analysisResult && (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl ${analysisResult.success ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'}`}>
                  <p className={`font-bold ${analysisResult.success ? 'text-emerald-700' : 'text-red-700'}`}>
                    {analysisResult.message}
                  </p>
                </div>

                {analysisResult.detectedItems && analysisResult.detectedItems.length > 0 && (
                  <>
                    {/* Resumen por categoría */}
                    <CategorySummary items={analysisResult.detectedItems} />
                    
                    <div className="bg-indigo-50 rounded-xl overflow-hidden">
                      <div className="bg-indigo-100 px-4 py-2">
                        <p className="font-black text-indigo-800 text-sm uppercase">
                          Muebles Detectados ({analysisResult.detectedItems.length})
                        </p>
                      </div>
                      <div className="max-h-60 overflow-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-indigo-100 sticky top-0">
                            <tr className="text-xs text-indigo-700 uppercase">
                              <th className="px-4 py-2 text-left">Código</th>
                              <th className="px-4 py-2 text-left">Descripción</th>
                              <th className="px-4 py-2 text-center">Tipo</th>
                              <th className="px-4 py-2 text-center">Ancho</th>
                              <th className="px-4 py-2 text-center">Alto</th>
                              <th className="px-4 py-2 text-center">Fondo</th>
                              <th className="px-4 py-2 text-center">Cant.</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-indigo-100">
                            {analysisResult.detectedItems.map((item, idx) => {
                              const category = classifyFurniture(item.productCode, item.productName);
                              const categoryColors = {
                                altos: 'bg-sky-100 text-sky-700',
                                bajos: 'bg-amber-100 text-amber-700',
                                columnas: 'bg-violet-100 text-violet-700',
                                especiales: 'bg-rose-100 text-rose-700'
                              };
                              return (
                                <tr key={idx} className="bg-white hover:bg-indigo-50">
                                  <td className="px-4 py-2 font-bold text-indigo-900">{item.productCode}</td>
                                  <td className="px-4 py-2 text-indigo-600">{item.productName}</td>
                                  <td className="px-4 py-2 text-center">
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${categoryColors[category]}`}>
                                      {category.charAt(0).toUpperCase() + category.slice(1)}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2 text-center">{item.width} cm</td>
                                  <td className="px-4 py-2 text-center">{item.height} cm</td>
                                  <td className="px-4 py-2 text-center">{item.depth} cm</td>
                                  <td className="px-4 py-2 text-center font-bold text-orange-600">{item.quantity}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Botón crear orden */}
                    <button
                      onClick={handleCreateOrder}
                      disabled={creatingOrder}
                      className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                      data-testid="create-order-from-pdf-btn"
                    >
                      {creatingOrder ? (
                        <>
                          <RefreshCw size={18} className="animate-spin" />
                          Creando orden...
                        </>
                      ) : (
                        <>
                          <Factory size={18} />
                          Crear Orden de Fabricación
                        </>
                      )}
                    </button>
                  </>
                )}

                {/* Notas del análisis */}
                {analysisResult.rawText && (
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <p className="text-xs font-bold text-amber-700 uppercase mb-1">Notas del análisis</p>
                    <p className="text-sm text-amber-800">{analysisResult.rawText}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-indigo-100 px-6 py-4 flex justify-end">
            <button
              onClick={() => { setShowImportModal(false); setAnalysisResult(null); setFile(null); }}
              className="px-6 py-2 border border-indigo-200 rounded-xl font-bold text-indigo-600 hover:bg-indigo-50"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-600 rounded-2xl">
              <Factory size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-indigo-950">Portal de Fábrica</h1>
              <p className="text-indigo-400 text-sm">Gestión de órdenes de fabricación</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowImportFromProjectsModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 flex items-center gap-2"
              data-testid="import-from-projects-btn"
            >
              <FolderOpen size={18} />
              Importar Pedido
            </button>
            <button
              onClick={() => setShowImportModal(true)}
              className="px-4 py-2 bg-white border border-indigo-200 rounded-xl font-bold text-indigo-600 hover:bg-indigo-50 flex items-center gap-2"
              data-testid="import-pdf-btn"
            >
              <Upload size={18} />
              Importar PDF
            </button>
            <button
              onClick={() => setShowNewOrderModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 flex items-center gap-2"
              data-testid="new-order-btn"
            >
              <Plus size={18} />
              Nueva Orden
            </button>
            <button
              onClick={loadData}
              className="p-2 bg-white border border-indigo-200 rounded-xl text-indigo-600 hover:bg-indigo-50"
              data-testid="refresh-btn"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Tabs de navegación */}
      <div className="bg-white rounded-2xl p-1 mb-6 flex items-center gap-1 shadow-sm border border-indigo-100 w-fit">
        <button
          onClick={() => setActiveTab('orders')}
          className={`px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
            activeTab === 'orders' 
              ? 'bg-indigo-600 text-white' 
              : 'text-indigo-600 hover:bg-indigo-50'
          }`}
          data-testid="tab-orders"
        >
          <Package size={16} />
          Órdenes
        </button>
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
            activeTab === 'dashboard' 
              ? 'bg-indigo-600 text-white' 
              : 'text-indigo-600 hover:bg-indigo-50'
          }`}
          data-testid="tab-dashboard"
        >
          <BarChart3 size={16} />
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${
            activeTab === 'history' 
              ? 'bg-indigo-600 text-white' 
              : 'text-indigo-600 hover:bg-indigo-50'
          }`}
          data-testid="tab-history"
        >
          <History size={16} />
          Historial
        </button>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'dashboard' ? (
        <ProductionDashboard 
          currentUser={currentUser}
          orders={filteredOrdersByFactory}
          factories={factories}
        />
      ) : activeTab === 'history' ? (
        <OrderHistory 
          orders={filteredOrdersByFactory}
          currentUser={currentUser}
          factories={factories}
        />
      ) : (
        <>
          {/* Stats Dashboard - Solo en pestaña órdenes */}
          {stats && (
            <div className="grid grid-cols-5 gap-4 mb-6">
              <StatCard 
                title="Activas" 
                value={stats.totalActive || 0} 
                icon={Package} 
                color="indigo"
                subtitle="Órdenes en proceso"
              />
              <StatCard 
                title="En Producción" 
                value={stats.byStatus?.in_production || 0} 
                icon={Factory} 
                color="amber"
              />
              <StatCard 
                title="Fabricadas" 
                value={stats.byStatus?.ready || 0} 
                icon={CheckCircle} 
                color="emerald"
              />
              <StatCard 
                title="Entrega Esta Semana" 
                value={stats.pendingThisWeek || 0} 
                icon={Truck} 
                color="blue"
              />
              <StatCard 
                title="Piezas Producción" 
                value={stats.piecesInProduction || 0} 
                icon={Box} 
                color="orange"
              />
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-2xl p-4 mb-6 flex items-center justify-between shadow-sm border border-indigo-100">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  placeholder="Buscar orden, cliente..."
                  className="pl-10 pr-4 py-2 border border-indigo-200 rounded-xl w-64 text-sm focus:border-indigo-500 outline-none"
                  data-testid="search-input"
                />
              </div>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="px-4 py-2 border border-indigo-200 rounded-xl text-sm font-bold text-indigo-700"
                data-testid="filter-status"
              >
                <option value="">Todos los estados</option>
                <option value="draft">Borrador</option>
                <option value="confirmed">Confirmada</option>
                <option value="in_production">En Producción</option>
                <option value="ready">Fabricada</option>
                <option value="delivered">Entregada</option>
              </select>
              <select
                value={filters.priority}
                onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                className="px-4 py-2 border border-indigo-200 rounded-xl text-sm font-bold text-indigo-700"
                data-testid="filter-priority"
              >
                <option value="">Todas las prioridades</option>
                <option value="low">Baja</option>
                <option value="normal">Normal</option>
                <option value="high">Alta</option>
                <option value="urgent">Urgente</option>
              </select>
              {/* Info de fábrica asignada */}
              {currentUser?.factoryId && (
                <span className="px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-xl text-sm font-bold flex items-center gap-2">
                  <Building2 size={14} />
                  {factories.find(f => f.id === currentUser.factoryId)?.name || 'Tu Fábrica'}
                </span>
              )}
            </div>
            <p className="text-sm text-indigo-400 font-bold">
              {filteredOrdersByFactory.length} órdenes encontradas
            </p>
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin">
                <RefreshCw size={32} className="text-indigo-600" />
              </div>
            </div>
          ) : (
            <OrderListView />
          )}
        </>
      )}

      {/* Modals */}
      {showNewOrderModal && <NewOrderModal />}
      {showDeliveryDateModal && <DeliveryDateModal />}
      {showImportModal && <ImportModal />}
      {showImportFromProjectsModal && <ImportFromProjectsModal />}
      
      {/* Modal de Despiece */}
      {showDespieceModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-orange-600 to-amber-600 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-xl font-black uppercase tracking-wider">
                  Despiece de Orden
                </h2>
                <p className="text-orange-100 text-sm">
                  {despieceData?.orderNumber} - {despieceData?.customerName}
                </p>
              </div>
              <button 
                onClick={() => { setShowDespieceModal(null); setDespieceData(null); }}
                className="p-2 hover:bg-white/20 rounded-xl transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
              {loadingDespiece ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw size={32} className="text-orange-600 animate-spin" />
                </div>
              ) : despieceData ? (
                <div className="space-y-6">
                  {despieceData.items?.map((item, itemIdx) => (
                    <div key={itemIdx} className="border border-orange-200 rounded-xl overflow-hidden">
                      {/* Item header */}
                      <div className="bg-orange-50 px-4 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-black text-orange-800">{item.productCode}</span>
                          <span className="text-orange-600">{item.productName}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 bg-orange-200 text-orange-800 rounded-full text-sm font-bold">
                            x{item.quantity}
                          </span>
                          <span className="text-sm text-orange-600">{item.dimensions}</span>
                        </div>
                      </div>
                      
                      {/* Components table */}
                      <table className="w-full">
                        <thead className="bg-orange-100/50">
                          <tr className="text-xs font-bold text-orange-700 uppercase">
                            <th className="px-4 py-2 text-left">Pieza</th>
                            <th className="px-4 py-2 text-left">Material</th>
                            <th className="px-4 py-2 text-center">Largo</th>
                            <th className="px-4 py-2 text-center">Ancho</th>
                            <th className="px-4 py-2 text-center">Espesor</th>
                            <th className="px-4 py-2 text-center">Cant.</th>
                            <th className="px-4 py-2 text-left">Notas</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-orange-100">
                          {item.components?.map((comp, compIdx) => (
                            <tr key={compIdx} className="hover:bg-orange-50/50">
                              <td className="px-4 py-2 font-medium text-gray-800">{comp.name}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{comp.material}</td>
                              <td className="px-4 py-2 text-center font-mono">{comp.length}</td>
                              <td className="px-4 py-2 text-center font-mono">{comp.width}</td>
                              <td className="px-4 py-2 text-center font-mono">{comp.thickness}</td>
                              <td className="px-4 py-2 text-center font-bold text-orange-700">{comp.quantity}</td>
                              <td className="px-4 py-2 text-xs text-gray-500">{comp.notes}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Scissors size={48} className="mx-auto text-orange-200 mb-4" />
                  <p className="text-orange-400">No hay datos de despiece</p>
                </div>
              )}
            </div>
            
            {/* Footer */}
            <div className="bg-orange-50 px-6 py-3 flex justify-end gap-3 border-t border-orange-200">
              <button
                onClick={() => { setShowDespieceModal(null); setDespieceData(null); }}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-300 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortalFabrica;
