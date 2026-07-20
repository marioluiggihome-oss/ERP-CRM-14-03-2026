/**
 * CarpinterosUsers — Gestión de usuarios de la división Carpinteros & Ebanistas.
 * El admin de la división (isCarpintero + canManageCarpinteroUsers) crea y
 * gestiona ÚNICAMENTE sus usuarios vinculados (linkedCarpinteroAdminId). Los
 * usuarios creados heredan el perfil carpintero, su landing y los permisos por
 * defecto de la división. Se abre desde el portal carpinteros.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { X, Plus, RefreshCw, Trash2, UserCheck, UserX, Users } from 'lucide-react';
import { authHeaders } from '../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;

export default function CarpinterosUsers({ onClose }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nuevo, setNuevo] = useState({ username: '', password: '', clientName: '' });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/api/users/carpinteros/mine`, { headers: authHeaders() });
      const data = await r.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch { setError('No se pudo cargar la lista'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const crear = async () => {
    setError('');
    if (!nuevo.username.trim() || !nuevo.password) { setError('Usuario y contraseña son obligatorios'); return; }
    setCreating(true);
    try {
      const r = await fetch(`${BASE}/api/users/carpinteros/create`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo),
      });
      const data = await r.json();
      if (!r.ok) { setError(data.detail || 'No se pudo crear'); return; }
      setNuevo({ username: '', password: '', clientName: '' });
      await load();
    } catch { setError('Error al crear el usuario'); }
    finally { setCreating(false); }
  };

  const toggle = async (u) => {
    try {
      await fetch(`${BASE}/api/users/carpinteros/toggle/${encodeURIComponent(u.id)}`, {
        method: 'PUT', headers: authHeaders(),
      });
      await load();
    } catch { setError('Error'); }
  };

  const borrar = async (u) => {
    if (!window.confirm(`¿Eliminar al usuario ${u.username}?`)) return;
    try {
      await fetch(`${BASE}/api/users/carpinteros/remove/${encodeURIComponent(u.id)}`, {
        method: 'DELETE', headers: authHeaders(),
      });
      await load();
    } catch { setError('Error'); }
  };

  return (
    <div className="fixed inset-0 z-[9998] bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 bg-stone-900 text-white">
          <h3 className="font-black flex items-center gap-2"><Users size={18} style={{ color: '#D4A373' }} /> Usuarios de mi división</h3>
          <button onClick={onClose} className="p-1.5 text-stone-400 hover:text-white"><X size={18} /></button>
        </div>

        {/* Alta */}
        <div className="p-4 bg-stone-50 border-b border-stone-200">
          <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wide mb-2">Nuevo usuario / cliente</p>
          <div className="flex items-center gap-2 flex-wrap">
            <input value={nuevo.username} onChange={e => setNuevo({ ...nuevo, username: e.target.value })}
              placeholder="Usuario" className="px-3 py-2 border border-stone-300 rounded-lg text-sm w-36" />
            <input value={nuevo.password} onChange={e => setNuevo({ ...nuevo, password: e.target.value })}
              type="password" placeholder="Contraseña" className="px-3 py-2 border border-stone-300 rounded-lg text-sm w-36" />
            <input value={nuevo.clientName} onChange={e => setNuevo({ ...nuevo, clientName: e.target.value })}
              placeholder="Nombre / empresa (opcional)" className="px-3 py-2 border border-stone-300 rounded-lg text-sm flex-1 min-w-[160px]" />
            <button onClick={crear} disabled={creating}
              className="px-4 py-2 bg-amber-700 hover:bg-amber-600 text-white rounded-lg text-xs font-black flex items-center gap-1.5 disabled:opacity-50">
              <Plus size={14} /> Crear
            </button>
          </div>
          <p className="text-[10px] text-stone-400 mt-2">El usuario hereda tu marca, tu web de inicio y los permisos de la división.</p>
          {error && <p className="text-xs text-red-600 font-bold mt-1">{error}</p>}
        </div>

        {/* Lista */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wide">{users.length} usuarios</p>
            <button onClick={load} className="p-1.5 rounded-lg bg-stone-100 hover:bg-stone-200"><RefreshCw size={14} className={loading ? 'animate-spin' : ''} /></button>
          </div>
          {users.length === 0 && !loading && (
            <p className="text-sm text-stone-400 text-center py-8">Aún no has creado usuarios.</p>
          )}
          <div className="space-y-2">
            {users.map(u => (
              <div key={u.id} className={`flex items-center gap-3 border rounded-xl px-3 py-2 ${u.isActive === false ? 'border-stone-200 bg-stone-50 opacity-60' : 'border-stone-200'}`}>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm text-stone-800 truncate">{u.username}</p>
                  <p className="text-[11px] text-stone-400 truncate">{u.clientName || '—'}{u.isActive === false ? ' · desactivado' : ''}</p>
                </div>
                <button onClick={() => toggle(u)} title={u.isActive === false ? 'Activar' : 'Desactivar'}
                  className={`p-1.5 rounded-lg ${u.isActive === false ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}`}>
                  {u.isActive === false ? <UserCheck size={15} /> : <UserX size={15} />}
                </button>
                <button onClick={() => borrar(u)} title="Eliminar" className="p-1.5 rounded-lg bg-red-50 text-red-500 hover:bg-red-100"><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
