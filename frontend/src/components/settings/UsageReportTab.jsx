/**
 * UsageReportTab - Informe de uso por usuario
 * Muestra estadísticas de actividad de los usuarios en la plataforma
 */
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from 'recharts';
import { Users, Activity, Calendar, TrendingUp, Download, RefreshCw, Clock, FileText, ShoppingCart, LogIn } from 'lucide-react';
import { authHeaders } from '../../services/api';

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b', '#06b6d4', '#84cc16'];

// Tarjeta de CONSUMO DE IA (solo master): contador mensual + umbral de alerta.
const KIND_LABELS = { render: 'Renders 3D', vision: 'Análisis de imagen', text: 'Texto', chat: 'Chat', search: 'Búsqueda', otro: 'Otros' };
const AIUsageCard = () => {
  const [data, setData] = useState(null);
  const [thr, setThr] = useState('');
  const [cRender, setCRender] = useState('');
  const [cVision, setCVision] = useState('');
  const [spendUrl, setSpendUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const load = async () => {
    try {
      const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/ai-usage`, { headers: authHeaders() });
      if (r.ok) {
        const d = await r.json(); setData(d);
        setThr(d.threshold ? String(d.threshold) : '');
        setCRender(d.cost_per?.render != null ? String(d.cost_per.render) : '');
        setCVision(d.cost_per?.vision != null ? String(d.cost_per.vision) : '');
        setSpendUrl(d.spend_url || '');
      }
    } catch {}
  };
  useEffect(() => { load(); }, []);
  const saveThreshold = async () => {
    setSaving(true);
    try {
      const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/ai-usage/threshold`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          threshold: Number(thr) || 0,
          cost_per: { render: Number(cRender) || 0, vision: Number(cVision) || 0 },
          spend_url: spendUrl || '',
        }),
      });
      if (r.ok) setData(await r.json());
    } catch {} finally { setSaving(false); }
  };
  if (!data) return null;
  const kinds = Object.entries(data.by_kind || {}).sort((a, b) => b[1] - a[1]);
  const barColor = data.over ? '#dc2626' : data.warn ? '#d97706' : '#4f46e5';
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><Activity className="w-4 h-4 text-indigo-500" /> Consumo de IA</h3>
          <p className="text-xs text-slate-400">Llamadas al motor de IA este mes ({data.current_month})</p>
        </div>
        <button onClick={load} className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100" title="Actualizar"><RefreshCw className="w-4 h-4" /></button>
      </div>
      <div className="flex items-end gap-3 mb-1 flex-wrap">
        <span className="text-4xl font-semibold tracking-tight text-slate-900 tabular-nums">{data.total.toLocaleString('es-ES')}</span>
        <span className="text-sm text-slate-500 mb-1">llamadas{data.threshold ? ` / ${data.threshold.toLocaleString('es-ES')}` : ''}</span>
        {data.estimated_cost > 0 && <span className="mb-1 text-sm font-semibold text-emerald-600 tabular-nums">≈ {data.estimated_cost.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} € estimado</span>}
        {data.over && <span className="mb-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">⚠ Límite superado</span>}
        {!data.over && data.warn && <span className="mb-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">⚠ Cerca del límite</span>}
      </div>
      {data.spend_url && (
        <a href={data.spend_url} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 mb-3">
          Ver coste real en el panel del proveedor ↗
        </a>
      )}
      {data.threshold > 0 && (
        <div className="h-2 rounded-full bg-slate-100 overflow-hidden mb-3">
          <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, data.pct)}%`, background: barColor }} />
        </div>
      )}
      {kinds.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {kinds.map(([k, v]) => (
            <span key={k} className="text-[11px] px-2 py-1 rounded-lg bg-slate-50 border border-slate-100 text-slate-600">
              {KIND_LABELS[k] || k}: <b className="text-slate-900 tabular-nums">{v.toLocaleString('es-ES')}</b>
            </span>
          ))}
        </div>
      )}
      <div className="border-t border-slate-100 pt-3 space-y-2.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 w-28">Alerta al superar</span>
          <input type="number" min="0" value={thr} onChange={e => setThr(e.target.value)} placeholder="sin límite"
            className="w-28 px-2 py-1 border border-slate-200 rounded-lg text-sm tabular-nums" />
          <span className="text-xs text-slate-400">llamadas/mes</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 w-28">Coste por llamada</span>
          <label className="flex items-center gap-1 text-xs text-slate-500">render
            <input type="number" step="0.001" min="0" value={cRender} onChange={e => setCRender(e.target.value)} placeholder="0"
              className="w-20 px-2 py-1 border border-slate-200 rounded-lg text-sm tabular-nums" />€</label>
          <label className="flex items-center gap-1 text-xs text-slate-500">visión
            <input type="number" step="0.001" min="0" value={cVision} onChange={e => setCVision(e.target.value)} placeholder="0"
              className="w-20 px-2 py-1 border border-slate-200 rounded-lg text-sm tabular-nums" />€</label>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 w-28">Panel del proveedor</span>
          <input type="url" value={spendUrl} onChange={e => setSpendUrl(e.target.value)} placeholder="https://…/spend"
            className="flex-1 min-w-[180px] px-2 py-1 border border-slate-200 rounded-lg text-sm" />
          <button onClick={saveThreshold} disabled={saving}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
};

const UsageReportTab = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/usage/report?days=${days}`, { headers: authHeaders() });
      if (!response.ok) throw new Error('Error cargando informe');
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [days]);

  const formatActivityType = (type) => {
    const labels = {
      'login': 'Inicios de sesión',
      'budget_create': 'Presupuestos creados',
      'budget_update': 'Presupuestos actualizados',
      'budget_export_pdf': 'PDFs exportados',
      'order_create': 'Pedidos creados',
      'order_confirm': 'Pedidos confirmados',
      'ai_telemetry': 'Uso IA Telemetría',
      'catalog_view': 'Vistas catálogo',
      'settings_update': 'Config. actualizada'
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-orange-500 animate-spin" />
        <span className="ml-3 text-slate-600 font-bold">Cargando informe...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600">
        <p className="font-bold">Error: {error}</p>
        <button onClick={fetchReport} className="mt-2 text-sm underline">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Consumo de IA (contador + umbral de alerta) */}
      <AIUsageCard />
      {/* Header con selector de período */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black text-slate-800 flex items-center gap-2">
            <Activity className="w-6 h-6 text-orange-500" />
            Informe de Uso
          </h2>
          <p className="text-sm text-slate-500">Estadísticas de actividad de usuarios</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold outline-none focus:border-orange-500"
          >
            <option value={7}>Últimos 7 días</option>
            <option value={30}>Últimos 30 días</option>
            <option value={90}>Últimos 90 días</option>
            <option value={365}>Último año</option>
          </select>
          <button
            onClick={fetchReport}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Resumen en tarjetas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-xs font-bold uppercase">Total Acciones</p>
              <p className="text-3xl font-black">{report?.summary?.totalActions || 0}</p>
            </div>
            <Activity className="w-10 h-10 text-orange-200" />
          </div>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-xs font-bold uppercase">Usuarios Activos</p>
              <p className="text-3xl font-black">{report?.summary?.activeUsers || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-200" />
          </div>
        </div>
        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-emerald-100 text-xs font-bold uppercase">Media por Usuario</p>
              <p className="text-3xl font-black">{report?.summary?.averageActionsPerUser || 0}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-emerald-200" />
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-xs font-bold uppercase">Período</p>
              <p className="text-3xl font-black">{days} días</p>
            </div>
            <Calendar className="w-10 h-10 text-purple-200" />
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-2 gap-6">
        {/* Actividad diaria */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="font-black text-slate-700 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-orange-500" />
            Actividad Diaria
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={report?.dailyActivity || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="totalActions" stroke="#f97316" strokeWidth={2} name="Acciones" />
              <Line type="monotone" dataKey="uniqueUsers" stroke="#3b82f6" strokeWidth={2} name="Usuarios" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Distribución por tipo */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="font-black text-slate-700 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            Actividad por Tipo
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={report?.activityByType?.map(a => ({ ...a, name: formatActivityType(a.activityType) })) || []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                fill="#8884d8"
                paddingAngle={2}
                dataKey="count"
                nameKey="name"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                labelLine={false}
              >
                {(report?.activityByType || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabla de usuarios */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
          <h3 className="font-black text-slate-700 flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-500" />
            Ranking de Usuarios por Actividad
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-100 text-xs font-black text-slate-600 uppercase">
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">Usuario</th>
                <th className="px-4 py-3 text-center">Total Acciones</th>
                <th className="px-4 py-3 text-center">
                  <span className="flex items-center justify-center gap-1">
                    <LogIn className="w-3 h-3" /> Logins
                  </span>
                </th>
                <th className="px-4 py-3 text-center">
                  <span className="flex items-center justify-center gap-1">
                    <FileText className="w-3 h-3" /> Presupuestos
                  </span>
                </th>
                <th className="px-4 py-3 text-center">
                  <span className="flex items-center justify-center gap-1">
                    <ShoppingCart className="w-3 h-3" /> Pedidos
                  </span>
                </th>
                <th className="px-4 py-3 text-center">PDFs</th>
                <th className="px-4 py-3 text-center">IA</th>
                <th className="px-4 py-3 text-left">Última Actividad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(report?.userStats || []).map((user, idx) => (
                <tr key={user._id || idx} className="hover:bg-orange-50/50 transition-colors">
                  <td className="px-4 py-3 text-sm">
                    {idx < 3 ? (
                      <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-black text-white ${
                        idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-slate-400' : 'bg-amber-700'
                      }`}>
                        {idx + 1}
                      </span>
                    ) : (
                      <span className="text-slate-400 font-bold">{idx + 1}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-black text-slate-800">{user.username}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-orange-100 text-orange-600 px-2 py-1 rounded-full text-xs font-black">
                      {user.totalActions}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-sm font-bold text-slate-600">{user.logins}</td>
                  <td className="px-4 py-3 text-center text-sm font-bold text-slate-600">
                    {(user.budgetsCreated || 0) + (user.budgetsUpdated || 0)}
                  </td>
                  <td className="px-4 py-3 text-center text-sm font-bold text-slate-600">
                    {(user.ordersCreated || 0) + (user.ordersConfirmed || 0)}
                  </td>
                  <td className="px-4 py-3 text-center text-sm font-bold text-slate-600">{user.pdfsExported || 0}</td>
                  <td className="px-4 py-3 text-center text-sm font-bold text-slate-600">{user.aiTelemetryUses || 0}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {user.lastActivity ? new Date(user.lastActivity).toLocaleString('es-ES') : '-'}
                  </td>
                </tr>
              ))}
              {(!report?.userStats || report.userStats.length === 0) && (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                    No hay datos de actividad en el período seleccionado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer con timestamp */}
      <div className="text-center text-xs text-slate-400">
        Informe generado: {report?.generatedAt ? new Date(report.generatedAt).toLocaleString('es-ES') : '-'}
      </div>
    </div>
  );
};

export default UsageReportTab;
