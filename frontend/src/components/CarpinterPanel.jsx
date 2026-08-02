/**
 * CarpinterPanel — Panel de gestión independiente para el admin de la división
 * Carpinter.io (canManageCarpinteroUsers && !isAdmin).
 *
 * Este panel REEMPLAZA completamente al SettingsModal cuando el usuario es
 * el administrador de la división carpinteros. No muestra NADA de Luiggi Home:
 * ni logos, ni tabs de Fábrica, Inventario, Red Distribución, etc.
 *
 * Secciones:
 *   - Usuarios: crear, activar/desactivar, eliminar usuarios de la división
 *   - Estadísticas: actividad y renders del equipo
 *   - Mi perfil: cambiar nombre y contraseña propios
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  X, Plus, RefreshCw, Trash2, UserCheck, UserX, Users,
  BarChart3, Zap, Clock, User, Key, Save, Eye, EyeOff,
  CheckCircle2, AlertCircle, ChevronRight
} from 'lucide-react';
import CarpinterLogo, { CarpinterMark } from './CarpinterLogo';
import { authHeaders } from '../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;
const fechaCorta = (s) =>
  s ? new Date(s).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: '2-digit' }) : '—';

/* ─── Sub-panel: Usuarios ─────────────────────────────────────────────────── */
function PanelUsuarios() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nuevo, setNuevo] = useState({ username: '', password: '', clientName: '' });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/api/users/carpinteros/mine`, { headers: authHeaders() });
      const data = await r.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch {
      setError('No se pudo cargar la lista de usuarios');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const crear = async () => {
    setError('');
    if (!nuevo.username.trim() || !nuevo.password) {
      setError('Usuario y contraseña son obligatorios');
      return;
    }
    setCreating(true);
    try {
      const r = await fetch(`${BASE}/api/users/carpinteros/create`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo),
      });
      const data = await r.json();
      if (!r.ok) { setError(data.detail || 'No se pudo crear el usuario'); return; }
      setNuevo({ username: '', password: '', clientName: '' });
      await load();
    } catch {
      setError('Error al crear el usuario');
    } finally {
      setCreating(false);
    }
  };

  const toggle = async (u) => {
    try {
      await fetch(`${BASE}/api/users/carpinteros/toggle/${encodeURIComponent(u.id)}`, {
        method: 'PUT', headers: authHeaders(),
      });
      await load();
    } catch { setError('Error al cambiar estado'); }
  };

  const borrar = async (u) => {
    if (!window.confirm(`¿Eliminar al usuario "${u.username}"? Esta acción no se puede deshacer.`)) return;
    try {
      await fetch(`${BASE}/api/users/carpinteros/remove/${encodeURIComponent(u.id)}`, {
        method: 'DELETE', headers: authHeaders(),
      });
      await load();
    } catch { setError('Error al eliminar'); }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Formulario de alta */}
      <div className="p-5 bg-orange-50 border-b border-orange-100">
        <p className="text-[11px] font-black text-orange-700 uppercase tracking-widest mb-3 flex items-center gap-1.5">
          <Plus size={12} /> Nuevo usuario / cliente
        </p>
        <div className="flex flex-wrap gap-2">
          <input
            value={nuevo.username}
            onChange={e => setNuevo({ ...nuevo, username: e.target.value })}
            onKeyDown={e => e.key === 'Enter' && crear()}
            placeholder="Usuario (login)"
            className="px-3 py-2 border border-orange-200 rounded-lg text-sm w-36 bg-white focus:outline-none focus:border-orange-500"
          />
          <div className="relative">
            <input
              value={nuevo.password}
              onChange={e => setNuevo({ ...nuevo, password: e.target.value })}
              onKeyDown={e => e.key === 'Enter' && crear()}
              type={showPass ? 'text' : 'password'}
              placeholder="Contraseña"
              className="px-3 py-2 pr-9 border border-orange-200 rounded-lg text-sm w-36 bg-white focus:outline-none focus:border-orange-500"
            />
            <button
              type="button"
              onClick={() => setShowPass(v => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              {showPass ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
          <input
            value={nuevo.clientName}
            onChange={e => setNuevo({ ...nuevo, clientName: e.target.value })}
            onKeyDown={e => e.key === 'Enter' && crear()}
            placeholder="Nombre / empresa (opcional)"
            className="px-3 py-2 border border-orange-200 rounded-lg text-sm flex-1 min-w-[160px] bg-white focus:outline-none focus:border-orange-500"
          />
          <button
            onClick={crear}
            disabled={creating}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-black flex items-center gap-1.5 disabled:opacity-50 transition-colors"
          >
            {creating ? <RefreshCw size={13} className="animate-spin" /> : <Plus size={13} />}
            Crear
          </button>
        </div>
        <p className="text-[10px] text-orange-500 mt-2">
          El usuario hereda tu marca, tu web de inicio y los permisos de la división carpinteros.
        </p>
        {error && (
          <p className="text-xs text-red-600 font-bold mt-2 flex items-center gap-1">
            <AlertCircle size={12} /> {error}
          </p>
        )}
      </div>

      {/* Lista de usuarios */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest">
            {users.length} usuario{users.length !== 1 ? 's' : ''} en tu división
          </p>
          <button
            onClick={load}
            className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
            title="Actualizar"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-orange-500' : 'text-slate-500'} />
          </button>
        </div>

        {loading && users.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw size={20} className="animate-spin text-orange-400" />
          </div>
        )}

        {!loading && users.length === 0 && (
          <div className="text-center py-12">
            <Users size={32} className="mx-auto text-slate-300 mb-3" />
            <p className="text-sm text-slate-400">Aún no has creado usuarios.</p>
            <p className="text-xs text-slate-300 mt-1">Crea el primero con el formulario de arriba.</p>
          </div>
        )}

        <div className="space-y-2">
          {users.map(u => (
            <div
              key={u.id}
              className={`flex items-center gap-3 border rounded-xl px-4 py-3 transition-colors ${
                u.isActive === false
                  ? 'border-slate-200 bg-slate-50 opacity-60'
                  : 'border-orange-100 bg-white hover:border-orange-200'
              }`}
            >
              <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
                <span className="text-xs font-black text-orange-600">
                  {(u.clientName || u.username || '?').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-sm text-slate-800 truncate">{u.username}</p>
                <p className="text-[11px] text-slate-400 truncate">
                  {u.clientName || '—'}
                  {u.isActive === false && <span className="text-red-400 ml-1">· desactivado</span>}
                </p>
              </div>
              <button
                onClick={() => toggle(u)}
                title={u.isActive === false ? 'Activar usuario' : 'Desactivar usuario'}
                className={`p-2 rounded-lg transition-colors ${
                  u.isActive === false
                    ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                    : 'bg-amber-50 text-amber-600 hover:bg-amber-100'
                }`}
              >
                {u.isActive === false ? <UserCheck size={15} /> : <UserX size={15} />}
              </button>
              <button
                onClick={() => borrar(u)}
                title="Eliminar usuario"
                className="p-2 rounded-lg bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Sub-panel: Estadísticas ─────────────────────────────────────────────── */
function PanelEstadisticas() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${BASE}/api/users/carpinteros/stats`, { headers: authHeaders() });
        const d = await r.json();
        setStats(d.success ? d : null);
      } catch { /* noop */ }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw size={24} className="animate-spin text-orange-400" />
      </div>
    );
  }

  return (
    <div className="p-5 overflow-y-auto h-full">
      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-orange-50 border border-orange-100 rounded-xl p-4">
          <div className="text-[10px] font-black text-orange-500 uppercase tracking-widest flex items-center gap-1">
            <Users size={11} /> Usuarios
          </div>
          <div className="text-3xl font-black text-slate-800 mt-1">{stats?.total ?? '—'}</div>
        </div>
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
          <div className="text-[10px] font-black text-emerald-600 uppercase tracking-widest flex items-center gap-1">
            <Clock size={11} /> Con actividad
          </div>
          <div className="text-3xl font-black text-emerald-700 mt-1">{stats?.conActividad ?? '—'}</div>
        </div>
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
          <div className="text-[10px] font-black text-amber-600 uppercase tracking-widest flex items-center gap-1">
            <Zap size={11} /> Renders/mes
          </div>
          <div className="text-3xl font-black text-amber-700 mt-1">{stats?.rendersTotales ?? '—'}</div>
        </div>
      </div>

      {/* Tabla de actividad */}
      {stats?.items && stats.items.length > 0 ? (
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="text-left p-3 text-[10px] font-black uppercase tracking-wide">Usuario</th>
                <th className="text-left p-3 text-[10px] font-black uppercase tracking-wide">Último acceso</th>
                <th className="text-right p-3 text-[10px] font-black uppercase tracking-wide">Accesos</th>
                <th className="text-right p-3 text-[10px] font-black uppercase tracking-wide">Renders/mes</th>
              </tr>
            </thead>
            <tbody>
              {stats.items.map(it => (
                <tr key={it.id} className={`border-t border-slate-100 ${it.isActive === false ? 'opacity-50' : ''}`}>
                  <td className="p-3">
                    <span className="font-bold text-slate-700 text-xs">{it.clientName || it.username}</span>
                    {it.esAdmin && <span className="ml-1 text-[9px] text-orange-600 font-black">admin</span>}
                  </td>
                  <td className="p-3 text-xs text-slate-400">{fechaCorta(it.ultimoLogin)}</td>
                  <td className="p-3 text-right text-xs text-slate-600 font-bold">{it.logins}</td>
                  <td className="p-3 text-right text-xs text-amber-600 font-bold">{it.rendersMes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400">
          <BarChart3 size={32} className="mx-auto mb-3 text-slate-300" />
          <p className="text-sm">Sin datos de actividad todavía.</p>
        </div>
      )}
    </div>
  );
}

/* ─── Sub-panel: Mi Perfil ────────────────────────────────────────────────── */
function PanelPerfil({ currentUser }) {
  const [clientName, setClientName] = useState(currentUser?.clientName || '');
  const [currentPass, setCurrentPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null); // { type: 'ok'|'error', text }

  const saveProfile = async () => {
    if (newPass && newPass !== confirmPass) {
      setMsg({ type: 'error', text: 'Las contraseñas nuevas no coinciden' });
      return;
    }
    if (newPass && newPass.length < 6) {
      setMsg({ type: 'error', text: 'La contraseña debe tener al menos 6 caracteres' });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      const body = { clientName };
      if (newPass) body.password = newPass;
      const r = await fetch(`${BASE}/api/users/${encodeURIComponent(currentUser.id)}`, {
        method: 'PUT',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) {
        setMsg({ type: 'error', text: data.detail || 'No se pudo guardar' });
        return;
      }
      setMsg({ type: 'ok', text: 'Perfil actualizado correctamente' });
      setCurrentPass('');
      setNewPass('');
      setConfirmPass('');
    } catch {
      setMsg({ type: 'error', text: 'Error de conexión' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 overflow-y-auto h-full">
      <div className="max-w-md mx-auto space-y-6">
        {/* Avatar / info */}
        <div className="flex items-center gap-4 p-4 bg-orange-50 border border-orange-100 rounded-xl">
          <div className="w-14 h-14 rounded-2xl bg-orange-600 flex items-center justify-center shrink-0">
            <span className="text-2xl font-black text-white">
              {(currentUser?.clientName || currentUser?.username || '?').charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-black text-slate-800">{currentUser?.username}</p>
            <p className="text-xs text-orange-600 font-bold">Admin de división · Carpinter.io</p>
          </div>
        </div>

        {/* Nombre / empresa */}
        <div>
          <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest block mb-2">
            Nombre / empresa
          </label>
          <input
            value={clientName}
            onChange={e => setClientName(e.target.value)}
            placeholder="Tu nombre o empresa"
            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:border-orange-400 transition-colors"
          />
        </div>

        {/* Cambiar contraseña */}
        <div>
          <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest block mb-2">
            <Key size={11} className="inline mr-1" /> Cambiar contraseña
          </label>
          <div className="space-y-2">
            <div className="relative">
              <input
                value={newPass}
                onChange={e => setNewPass(e.target.value)}
                type={showNew ? 'text' : 'password'}
                placeholder="Nueva contraseña"
                className="w-full px-4 py-2.5 pr-10 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:border-orange-400 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowNew(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showNew ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <input
              value={confirmPass}
              onChange={e => setConfirmPass(e.target.value)}
              type="password"
              placeholder="Repetir nueva contraseña"
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:border-orange-400 transition-colors"
            />
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5">Deja en blanco si no quieres cambiar la contraseña.</p>
        </div>

        {/* Mensaje de estado */}
        {msg && (
          <div className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-bold ${
            msg.type === 'ok'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-red-50 text-red-600 border border-red-200'
          }`}>
            {msg.type === 'ok' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            {msg.text}
          </div>
        )}

        {/* Botón guardar */}
        <button
          onClick={saveProfile}
          disabled={saving}
          className="w-full py-3 bg-orange-600 hover:bg-orange-500 text-white rounded-xl font-black text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors"
        >
          {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
          Guardar cambios
        </button>
      </div>
    </div>
  );
}

/* ─── Panel principal ─────────────────────────────────────────────────────── */
export default function CarpinterPanel({ isOpen, onClose, currentUser }) {
  const [tab, setTab] = useState('usuarios');

  if (!isOpen) return null;

  const tabs = [
    { id: 'usuarios', label: 'Usuarios', icon: Users },
    { id: 'stats', label: 'Estadísticas', icon: BarChart3 },
    { id: 'perfil', label: 'Mi perfil', icon: User },
  ];

  return (
    <div
      className="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-2xl max-h-[88vh] flex flex-col overflow-hidden shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header con branding Carpinter */}
        <div className="bg-slate-950 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <CarpinterMark size={32} />
            <div>
              <p className="text-white font-black text-sm leading-none">
                carpinter<span className="text-orange-500">.io</span>
              </p>
              <p className="text-slate-400 text-[10px] font-medium mt-0.5 uppercase tracking-widest">
                Panel de administración
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tabs de navegación */}
        <div className="flex gap-0 bg-slate-50 border-b border-slate-200 shrink-0">
          {tabs.map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-5 py-3 text-xs font-black uppercase tracking-widest transition-colors border-b-2 ${
                  tab === t.id
                    ? 'border-orange-500 text-orange-600 bg-white'
                    : 'border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Icon size={14} />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Contenido del tab activo */}
        <div className="flex-1 overflow-hidden">
          {tab === 'usuarios' && <PanelUsuarios />}
          {tab === 'stats' && <PanelEstadisticas />}
          {tab === 'perfil' && <PanelPerfil currentUser={currentUser} />}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
          <p className="text-[9px] font-black text-slate-300 uppercase tracking-widest">
            CARPINTER.IO ERP · División Carpinteros & Ebanistas
          </p>
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-slate-600 font-bold flex items-center gap-1 transition-colors"
          >
            Cerrar <ChevronRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}
