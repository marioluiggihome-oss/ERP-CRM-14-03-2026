/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * SubscriptionTab — Panel de Suscripciones SaaS
 * Gestión de planes y créditos de IA por usuario (solo Admin/Master)
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  CreditCard, Users, Zap, RefreshCw, ChevronDown, Check,
  AlertTriangle, Star, Building2, Briefcase, User, Settings,
  TrendingUp, Lock, Unlock, X, Save, Info
} from 'lucide-react';
import { authHeaders } from '../../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;

// ─── Colores e iconos por plan ────────────────────────────────────────────────
const PLAN_META = {
  starter:     { icon: User,      gradient: 'from-indigo-500 to-indigo-600',    badge: 'bg-indigo-100 text-indigo-700',  ring: 'ring-indigo-400' },
  profesional: { icon: Briefcase, gradient: 'from-cyan-500 to-cyan-600',        badge: 'bg-cyan-100 text-cyan-700',      ring: 'ring-cyan-400' },
  business:    { icon: Building2, gradient: 'from-emerald-500 to-emerald-600',  badge: 'bg-emerald-100 text-emerald-700',ring: 'ring-emerald-400' },
  enterprise:  { icon: Star,      gradient: 'from-violet-500 to-violet-600',    badge: 'bg-violet-100 text-violet-700',  ring: 'ring-violet-400' },
  custom:      { icon: Settings,  gradient: 'from-slate-500 to-slate-600',      badge: 'bg-slate-100 text-slate-600',    ring: 'ring-slate-400' },
};

// ─── Barra de progreso de créditos ───────────────────────────────────────────
const CreditBar = ({ consumed, assigned, pct, over }) => {
  if (!assigned) return <span className="text-xs text-slate-400 italic">Sin límite / Admin</span>;
  const color = over ? 'bg-red-500' : pct >= 80 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>{consumed} / {assigned}</span>
        <span className={over ? 'text-red-600 font-bold' : pct >= 80 ? 'text-amber-600 font-semibold' : 'text-slate-500'}>
          {pct}%
        </span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      {over && (
        <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
          <AlertTriangle size={10} /> Créditos agotados
        </p>
      )}
    </div>
  );
};

// ─── Badge de plan ────────────────────────────────────────────────────────────
const PlanBadge = ({ planId, planName }) => {
  const meta = PLAN_META[planId] || PLAN_META.custom;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${meta.badge}`}>
      {planName || 'Sin plan'}
    </span>
  );
};

// ─── Modal de asignación de plan ─────────────────────────────────────────────
const AssignModal = ({ users, plans, onClose, onAssigned }) => {
  const [selectedUsers, setSelectedUsers] = useState(users.map(u => u.id));
  const [selectedPlan, setSelectedPlan] = useState('');
  const [customCredits, setCustomCredits] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const chosenPlan = plans.find(p => p.id === selectedPlan);

  const toggleUser = (id) => {
    setSelectedUsers(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    if (!selectedPlan) { setError('Selecciona un plan'); return; }
    if (!selectedUsers.length) { setError('Selecciona al menos un usuario'); return; }
    setSaving(true);
    setError('');
    try {
      const body = {
        user_ids: selectedUsers,
        plan_id: selectedPlan,
        notes,
      };
      if (selectedPlan === 'custom' && customCredits !== '') {
        body.custom_credits = parseInt(customCredits, 10) || 0;
      }
      const r = await fetch(`${BASE}/api/admin/subscription/assign`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Error al asignar');
      onAssigned(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <CreditCard size={20} className="text-indigo-500" />
            Asignar plan de suscripción
          </h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Selección de plan */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Plan</label>
            <div className="grid grid-cols-1 gap-2">
              {plans.map(plan => {
                const meta = PLAN_META[plan.id] || PLAN_META.custom;
                const Icon = meta.icon;
                const isSelected = selectedPlan === plan.id;
                return (
                  <button
                    key={plan.id}
                    onClick={() => { setSelectedPlan(plan.id); setCustomCredits(''); }}
                    className={`flex items-center gap-3 p-3 rounded-xl border-2 text-left transition-all ${
                      isSelected
                        ? `border-current bg-gradient-to-r ${meta.gradient} text-white shadow-md`
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className={`p-1.5 rounded-lg ${isSelected ? 'bg-white/20' : 'bg-slate-100'}`}>
                      <Icon size={16} className={isSelected ? 'text-white' : 'text-slate-600'} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm">{plan.name}</span>
                        {plan.price > 0 && (
                          <span className={`text-xs font-semibold ${isSelected ? 'text-white/80' : 'text-slate-500'}`}>
                            {plan.price}€/mes
                          </span>
                        )}
                      </div>
                      <p className={`text-xs truncate ${isSelected ? 'text-white/70' : 'text-slate-500'}`}>
                        {plan.aiCreditsMonthly > 0 ? `${plan.aiCreditsMonthly} renders IA/mes` : 'Créditos personalizados'} · {plan.description}
                      </p>
                    </div>
                    {isSelected && <Check size={16} className="text-white flex-shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Créditos personalizados (solo plan Custom) */}
          {selectedPlan === 'custom' && (
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Créditos de IA mensuales (renders)
              </label>
              <input
                type="number"
                min="0"
                value={customCredits}
                onChange={e => setCustomCredits(e.target.value)}
                placeholder="Ej: 60"
                className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          )}

          {/* Notas */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Notas internas (opcional)</label>
            <input
              type="text"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Ej: Cliente especial, descuento aplicado…"
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          {/* Selección de usuarios */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Usuarios ({selectedUsers.length} seleccionados)
            </label>
            <div className="space-y-1 max-h-48 overflow-y-auto border border-slate-100 rounded-xl p-2 bg-slate-50">
              {users.map(u => (
                <label key={u.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-white cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(u.id)}
                    onChange={() => toggleUser(u.id)}
                    className="rounded text-indigo-600"
                  />
                  <span className="text-sm text-slate-800 font-medium">{u.username}</span>
                  {u.clientName && <span className="text-xs text-slate-400">({u.clientName})</span>}
                  <PlanBadge planId={u.subscriptionPlan} planName={u.planName} />
                </label>
              ))}
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 rounded-xl px-3 py-2">
              <AlertTriangle size={14} /> {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !selectedPlan}
            className="px-5 py-2 rounded-xl text-sm font-bold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
            Guardar asignación
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────
const SubscriptionTab = () => {
  const [plans, setPlans] = useState([]);
  const [users, setUsers] = useState([]);
  const [creditsUsage, setCreditsUsage] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignTarget, setAssignTarget] = useState(null); // null = todos, o array de usuarios
  const [successMsg, setSuccessMsg] = useState('');
  const [activeView, setActiveView] = useState('users'); // 'users' | 'plans'
  const [searchQ, setSearchQ] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [rPlans, rUsers, rCredits] = await Promise.all([
        fetch(`${BASE}/api/admin/subscription/plans`, { headers: authHeaders() }),
        fetch(`${BASE}/api/admin/subscription/users`, { headers: authHeaders() }),
        fetch(`${BASE}/api/admin/subscription/credits-usage`, { headers: authHeaders() }),
      ]);
      const [dPlans, dUsers, dCredits] = await Promise.all([rPlans.json(), rUsers.json(), rCredits.json()]);
      if (dPlans.success) setPlans(dPlans.plans);
      if (dUsers.success) setUsers(dUsers.users);
      if (dCredits.success) setCreditsUsage(dCredits.users);
    } catch (e) {
      setError('Error cargando datos de suscripciones');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Combinar datos de usuarios con datos de créditos
  const enrichedUsers = users.map(u => {
    const credit = creditsUsage.find(c => c.id === u.id) || {};
    return { ...u, ...credit };
  });

  const filteredUsers = enrichedUsers.filter(u =>
    !searchQ ||
    u.username?.toLowerCase().includes(searchQ.toLowerCase()) ||
    u.clientName?.toLowerCase().includes(searchQ.toLowerCase()) ||
    u.planName?.toLowerCase().includes(searchQ.toLowerCase())
  );

  const handleAssignOne = (user) => {
    setAssignTarget([user]);
    setShowAssignModal(true);
  };

  const handleAssignAll = () => {
    setAssignTarget(filteredUsers);
    setShowAssignModal(true);
  };

  const handleAssigned = (result) => {
    setShowAssignModal(false);
    setSuccessMsg(`✓ Plan "${result.plan}" asignado a ${result.updated} usuario(s) con ${result.aiCreditsMonthly} créditos/mes`);
    setTimeout(() => setSuccessMsg(''), 5000);
    load();
  };

  // Estadísticas resumen
  const stats = {
    total: enrichedUsers.length,
    conPlan: enrichedUsers.filter(u => u.subscriptionPlan).length,
    sinPlan: enrichedUsers.filter(u => !u.subscriptionPlan).length,
    agotados: enrichedUsers.filter(u => u.over).length,
    ingresos: plans.reduce((acc, p) => {
      if (p.price === 0) return acc;
      const count = enrichedUsers.filter(u => u.subscriptionPlan === p.id).length;
      return acc + count * p.price;
    }, 0),
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={28} className="animate-spin text-indigo-400" />
        <span className="ml-3 text-slate-500 text-sm">Cargando suscripciones…</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
            <CreditCard size={22} className="text-indigo-500" />
            Suscripciones y Créditos IA
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">Gestiona los planes de suscripción y el consumo de créditos de IA por usuario</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-500 transition-colors"
            title="Actualizar"
          >
            <RefreshCw size={16} />
          </button>
          <button
            onClick={handleAssignAll}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors shadow-sm"
          >
            <CreditCard size={15} /> Asignar plan
          </button>
        </div>
      </div>

      {/* Mensaje de éxito */}
      {successMsg && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl px-4 py-3 text-sm font-medium">
          <Check size={16} /> {successMsg}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Tarjetas de resumen */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Usuarios totales</p>
          <p className="text-2xl font-black text-slate-900 mt-1">{stats.total}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Con plan activo</p>
          <p className="text-2xl font-black text-indigo-600 mt-1">{stats.conPlan}</p>
        </div>
        <div className={`bg-white border rounded-2xl p-4 shadow-sm ${stats.agotados > 0 ? 'border-red-200' : 'border-slate-200'}`}>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Créditos agotados</p>
          <p className={`text-2xl font-black mt-1 ${stats.agotados > 0 ? 'text-red-600' : 'text-slate-400'}`}>
            {stats.agotados}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">MRR estimado</p>
          <p className="text-2xl font-black text-emerald-600 mt-1">{stats.ingresos}€</p>
        </div>
      </div>

      {/* Navegación de vistas */}
      <div className="flex gap-2 bg-slate-100 rounded-xl p-1 w-fit">
        <button
          onClick={() => setActiveView('users')}
          className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
            activeView === 'users' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <span className="flex items-center gap-1.5"><Users size={14} /> Usuarios</span>
        </button>
        <button
          onClick={() => setActiveView('plans')}
          className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
            activeView === 'plans' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <span className="flex items-center gap-1.5"><Star size={14} /> Planes</span>
        </button>
      </div>

      {/* ── VISTA USUARIOS ── */}
      {activeView === 'users' && (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          {/* Buscador */}
          <div className="p-4 border-b border-slate-100">
            <input
              type="text"
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
              placeholder="Buscar usuario, cliente o plan…"
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>

          {/* Tabla */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Usuario</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Plan</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide min-w-[160px]">Créditos IA este mes</th>
                  <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Inicio</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center py-10 text-slate-400 text-sm">
                      No hay usuarios que coincidan con la búsqueda
                    </td>
                  </tr>
                )}
                {filteredUsers.map(u => (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900">{u.username}</div>
                      {u.clientName && <div className="text-xs text-slate-400">{u.clientName}</div>}
                      {!u.isActive && (
                        <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-600 font-medium">Inactivo</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <PlanBadge planId={u.subscriptionPlan} planName={u.planName} />
                      {u.subscriptionNotes && (
                        <p className="text-xs text-slate-400 mt-0.5 max-w-[140px] truncate" title={u.subscriptionNotes}>
                          {u.subscriptionNotes}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <CreditBar
                        consumed={u.consumed || 0}
                        assigned={u.assigned || u.aiCreditsMonthly || 0}
                        pct={u.pct || 0}
                        over={u.over || false}
                      />
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {u.subscriptionStartDate || '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleAssignOne(u)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors flex items-center gap-1 ml-auto"
                      >
                        <ChevronDown size={12} /> Plan
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── VISTA PLANES ── */}
      {activeView === 'plans' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {plans.map(plan => {
            const meta = PLAN_META[plan.id] || PLAN_META.custom;
            const Icon = meta.icon;
            const usersOnPlan = enrichedUsers.filter(u => u.subscriptionPlan === plan.id);
            return (
              <div
                key={plan.id}
                className={`bg-white border-2 rounded-2xl shadow-sm overflow-hidden transition-shadow hover:shadow-md ${
                  plan.id === 'business' ? 'border-emerald-300' : 'border-slate-200'
                }`}
              >
                {/* Header del plan */}
                <div className={`bg-gradient-to-r ${meta.gradient} p-4 text-white`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-white/20 rounded-xl">
                        <Icon size={18} />
                      </div>
                      <div>
                        <h3 className="font-black text-lg leading-tight">{plan.name}</h3>
                        {plan.price > 0 && (
                          <p className="text-white/80 text-sm font-semibold">{plan.price}€/mes</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-black">{usersOnPlan.length}</div>
                      <div className="text-xs text-white/70">usuarios</div>
                    </div>
                  </div>
                  <p className="text-white/70 text-xs mt-2">{plan.description}</p>
                </div>

                {/* Créditos IA */}
                <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
                  <Zap size={14} className="text-amber-500" />
                  <span className="text-sm font-semibold text-slate-700">
                    {plan.aiCreditsMonthly > 0 ? `${plan.aiCreditsMonthly} renders IA/mes` : 'Créditos personalizados'}
                  </span>
                </div>

                {/* Features */}
                <div className="p-4 space-y-1.5">
                  {(plan.features || []).map((f, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-600">
                      <Check size={12} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                      <span>{f}</span>
                    </div>
                  ))}
                </div>

                {/* Usuarios en este plan */}
                {usersOnPlan.length > 0 && (
                  <div className="px-4 pb-4">
                    <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Usuarios activos</p>
                    <div className="flex flex-wrap gap-1">
                      {usersOnPlan.map(u => (
                        <span
                          key={u.id}
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700 font-medium"
                          title={u.clientName}
                        >
                          {u.username}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Botón asignar */}
                <div className="px-4 pb-4">
                  <button
                    onClick={() => {
                      setAssignTarget(enrichedUsers);
                      setShowAssignModal(true);
                    }}
                    className={`w-full py-2 rounded-xl text-sm font-bold bg-gradient-to-r ${meta.gradient} text-white hover:opacity-90 transition-opacity shadow-sm`}
                  >
                    Asignar este plan
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Nota informativa */}
      <div className="flex items-start gap-2 bg-blue-50 border border-blue-100 rounded-xl p-3 text-xs text-blue-700">
        <Info size={14} className="mt-0.5 flex-shrink-0 text-blue-500" />
        <span>
          Los administradores y gerentes tienen <strong>créditos ilimitados</strong> independientemente del plan asignado.
          Los créditos se reinician el primer día de cada mes. El coste estimado por render es de <strong>~0,20€</strong> (Gemini Pro Image).
        </span>
      </div>

      {/* Modal de asignación */}
      {showAssignModal && (
        <AssignModal
          users={assignTarget || enrichedUsers}
          plans={plans}
          onClose={() => setShowAssignModal(false)}
          onAssigned={handleAssigned}
        />
      )}
    </div>
  );
};

export default SubscriptionTab;
