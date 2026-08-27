/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados.
 * Gestión acotada de usuarios de un estudio/tienda Studio3K.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { X, Plus, RefreshCw, Trash2, UserCheck, UserX, Users } from 'lucide-react';
import { authHeaders } from '../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;

export default function Studio3kUsers({ onClose }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [nuevo, setNuevo] = useState({ username: '', password: '', clientName: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE}/api/users/studio3k/mine`, { headers: authHeaders() });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || 'No se pudo cargar la lista');
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'No se pudo cargar la lista');
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
      const response = await fetch(`${BASE}/api/users/studio3k/create`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || 'No se pudo crear el usuario');
      setNuevo({ username: '', password: '', clientName: '' });
      await load();
    } catch (err) {
      setError(err.message || 'Error al crear el usuario');
    } finally {
      setCreating(false);
    }
  };

  const toggle = async (user) => {
    setError('');
    try {
      const response = await fetch(`${BASE}/api/users/studio3k/toggle/${encodeURIComponent(user.id)}`, {
        method: 'PUT', headers: authHeaders(),
      });
      if (!response.ok) throw new Error('No se pudo actualizar el usuario');
      await load();
    } catch (err) {
      setError(err.message || 'No se pudo actualizar el usuario');
    }
  };

  const borrar = async (user) => {
    if (!window.confirm(`¿Eliminar al usuario ${user.username}?`)) return;
    setError('');
    try {
      const response = await fetch(`${BASE}/api/users/studio3k/remove/${encodeURIComponent(user.id)}`, {
        method: 'DELETE', headers: authHeaders(),
      });
      if (!response.ok) throw new Error('No se pudo eliminar el usuario');
      await load();
    } catch (err) {
      setError(err.message || 'No se pudo eliminar el usuario');
    }
  };

  return (
    <div className="fixed inset-0 z-[9998] bg-slate-950/70 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 bg-[#0a0d15] text-white">
          <div>
            <h3 className="font-black flex items-center gap-2"><Users size={18} className="text-[#5f78ca]" /> Usuarios Studio3K</h3>
            <p className="text-[11px] text-slate-400 mt-1">Usuarios de tu estudio con acceso a Estudio 3D.</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white" aria-label="Cerrar"><X size={18} /></button>
        </div>

        <div className="p-4 bg-slate-50 border-b border-slate-200">
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mb-2">Nuevo usuario del estudio</p>
          <div className="flex items-center gap-2 flex-wrap">
            <input value={nuevo.username} onChange={(event) => setNuevo({ ...nuevo, username: event.target.value })}
              placeholder="Usuario" className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-36" />
            <input value={nuevo.password} onChange={(event) => setNuevo({ ...nuevo, password: event.target.value })}
              type="password" placeholder="Contraseña" className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-36" />
            <input value={nuevo.clientName} onChange={(event) => setNuevo({ ...nuevo, clientName: event.target.value })}
              placeholder="Nombre (opcional)" className="px-3 py-2 border border-slate-300 rounded-lg text-sm flex-1 min-w-[160px]" />
            <button onClick={crear} disabled={creating}
              className="px-4 py-2 bg-[#5f78ca] hover:bg-[#4d66b5] text-white rounded-lg text-xs font-black flex items-center gap-1.5 disabled:opacity-50">
              <Plus size={14} /> Crear
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mt-2">Cada usuario queda vinculado a tu estudio y hereda el acceso a Estudio 3D.</p>
          {error && <p className="text-xs text-red-600 font-bold mt-2">{error}</p>}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">{users.length} usuarios</p>
            <button onClick={load} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200" aria-label="Actualizar">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          {!users.length && !loading && <p className="text-sm text-slate-400 text-center py-8">Aún no has creado usuarios para tu estudio.</p>}
          <div className="space-y-2">
            {users.map((user) => (
              <div key={user.id} className={`flex items-center gap-3 border rounded-xl px-3 py-2 ${user.isActive === false ? 'border-slate-200 bg-slate-50 opacity-60' : 'border-slate-200'}`}>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm text-slate-800 truncate">{user.username}</p>
                  <p className="text-[11px] text-slate-400 truncate">{user.clientName || '—'}{user.isActive === false ? ' · desactivado' : ''}</p>
                </div>
                <button onClick={() => toggle(user)} title={user.isActive === false ? 'Activar' : 'Desactivar'}
                  className={`p-1.5 rounded-lg ${user.isActive === false ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-700'}`}>
                  {user.isActive === false ? <UserCheck size={15} /> : <UserX size={15} />}
                </button>
                <button onClick={() => borrar(user)} title="Eliminar" className="p-1.5 rounded-lg bg-red-50 text-red-500"><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
