/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Users, Loader, AlertTriangle, Check } from 'lucide-react';
import { usersAPI } from '../services/api';
import { plataformaDe, NOMBRES, COOPERATIVA } from '../plataformas';

/**
 * LOS USUARIOS DE LA COOPERATIVA, Y QUIÉN ES SOCIO.
 *
 * El master, 28/08: «faltarían los usuarios también ahí, en ese espacio COOP».
 * Antes había que ir al panel Master, buscar al usuario y bajar hasta las dos
 * casillas. Aquí se ve de un vistazo quién es socio y se marca en el sitio.
 *
 * SOLO SALEN LOS DE LA COOPERATIVA. Los suscriptores de carpinter.io y Studio3K
 * comparten la tabla de usuarios pero no tienen nada que ver con este negocio
 * (CLAUDE.md, regla 21), y enseñarlos aquí sería invitar a marcar como socio a
 * quien no puede serlo.
 *
 * MARCAR AQUÍ ES DINERO: quien lleve una de las dos marcas entra en la
 * liquidación. Por eso se dice en la propia pantalla y por eso se recarga desde
 * el servidor después de cada cambio, en vez de creerse el estado local.
 */
export default function CoopUsuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState('');
  const [hecho, setHecho] = useState('');
  const [abierto, setAbierto] = useState(false);
  const [nuevo, setNuevo] = useState({ username: '', password: '', clientName: '', rol: 'montador' });

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const d = await usersAPI.getAll();
      const lista = Array.isArray(d) ? d : (d.users || []);
      setUsuarios(lista.filter((u) => plataformaDe(u) === COOPERATIVA));
      setError('');
    } catch {
      setError('No se pudo cargar la lista de usuarios.');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const marcar = async (u, campo, valor) => {
    setGuardando(u.id);
    try {
      await usersAPI.update(u.id, { [campo]: valor });
      await cargar();
      setHecho(u.id);
      setTimeout(() => setHecho(''), 2000);
    } catch {
      setError('No se pudo guardar el cambio.');
    } finally {
      setGuardando('');
    }
  };

  /**
   * ALTA DE UN SOCIO DESDE AQUÍ.
   *
   * El master, 28/08: «vamos a crear un usuario para usuario cooperativista
   * montador; genera ese perfil para acceder a ese usuario desde el máster, en
   * la sección COOP, creación de usuarios».
   *
   * Se crea YA MARCADO con su rol de socio —es a lo que se viene a esta
   * pantalla— y con la plataforma de la cooperativa, que es la única que
   * reparte comisiones. Los permisos del ERP se quedan en lo mínimo: un
   * montador entra a ver lo suyo, no a presupuestar. Lo demás se le da luego en
   * el panel Master, a conciencia.
   */
  const crear = async () => {
    if (!nuevo.username || !nuevo.password || !nuevo.clientName) {
      setError('Hacen falta usuario, contraseña y nombre.'); return;
    }
    setGuardando('nuevo');
    try {
      await usersAPI.create({
        username: nuevo.username.trim(),
        password: nuevo.password,
        clientName: nuevo.clientName.trim(),
        plataforma: COOPERATIVA,
        esCooperativistaMontador: nuevo.rol === 'montador',
        esCooperativistaComercial: nuevo.rol === 'comercial',
        // Marcarlo montador de la agenda si lo es, para poder vincular su ficha.
        isMontador: nuevo.rol === 'montador',
        isActive: true,
      });
      setNuevo({ username: '', password: '', clientName: '', rol: 'montador' });
      setAbierto(false);
      await cargar();
      setError('');
    } catch (e) {
      setError(e.message || 'No se pudo crear el usuario.');
    } finally {
      setGuardando('');
    }
  };

  if (cargando && usuarios.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-dato-500">
        <Loader className="animate-spin mr-2" size={18} /> Cargando…
      </div>
    );
  }

  const socios = usuarios.filter(
    (u) => u.esCooperativistaComercial || u.esCooperativistaMontador);

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-8 py-6">
        <h1 className="text-xl font-black text-dato-800 tracking-tight flex items-center gap-2">
          <Users size={20} /> Usuarios de la cooperativa
        </h1>
        <p className="text-xs text-dato-500 mt-1 mb-4">
          Quién es socio. Marcar aquí mete a esa persona en la liquidación, así que
          solo lo tocas tú. {socios.length} de {usuarios.length} son socios.
        </p>

        {error && (
          <div className="mb-4 rounded-xl border border-error-300 bg-error-50 px-3 py-2 text-xs font-bold text-error-700">
            {error}
          </div>
        )}

        <div className="mb-4">
          <button
            onClick={() => setAbierto(v => !v)}
            className="px-3 py-1.5 rounded-lg bg-master-600 text-white text-[11px] font-black uppercase tracking-widest hover:bg-master-700 transition-colors"
            data-testid="coop-crear-usuario-btn"
          >
            {abierto ? 'Cancelar' : '+ Nuevo socio'}
          </button>
          {abierto && (
            <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Nombre</span>
                <input
                  value={nuevo.clientName}
                  onChange={(e) => setNuevo({ ...nuevo, clientName: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800"
                  data-testid="coop-nuevo-nombre"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Rol</span>
                <select
                  value={nuevo.rol}
                  onChange={(e) => setNuevo({ ...nuevo, rol: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800 bg-white"
                  data-testid="coop-nuevo-rol"
                >
                  <option value="montador">Montador cooperativista</option>
                  <option value="comercial">Comercial cooperativista</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Usuario</span>
                <input
                  value={nuevo.username}
                  autoComplete="off"
                  onChange={(e) => setNuevo({ ...nuevo, username: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800"
                  data-testid="coop-nuevo-usuario"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Contraseña</span>
                <input
                  type="password"
                  value={nuevo.password}
                  autoComplete="new-password"
                  onChange={(e) => setNuevo({ ...nuevo, password: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800"
                  data-testid="coop-nuevo-password"
                />
              </label>
              <div className="sm:col-span-2 flex items-center gap-3 flex-wrap">
                <button
                  onClick={crear}
                  disabled={guardando === 'nuevo'}
                  className="px-3 py-1.5 rounded-lg bg-ok-600 text-white text-[11px] font-black uppercase tracking-widest disabled:opacity-40 hover:bg-ok-700 transition-colors"
                  data-testid="coop-nuevo-guardar"
                >
                  {guardando === 'nuevo' ? 'Creando…' : 'Crear socio'}
                </button>
                <span className="text-[11px] text-dato-500">
                  Se crea en la red de distribución y ya marcado como socio. Los
                  permisos del ERP se los das luego en el panel Master.
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="mb-3 rounded-xl border border-aviso-300 bg-aviso-50 px-3 py-2 text-[11px] font-bold text-aviso-800 flex items-start gap-2">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            El comercial y el montador en nómina, y los montadores externos, NO son
            socios: montan y venden igual, y no cobran comisión. Socio es solo quien
            lleva una de estas dos marcas.
          </span>
        </div>

        {usuarios.length === 0 ? (
          <p className="text-sm text-dato-500">No hay usuarios en la cooperativa.</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-dato-500">
                <tr>
                  <th className="text-left font-black uppercase tracking-wide px-3 py-2">Usuario</th>
                  <th className="text-center font-black uppercase tracking-wide px-3 py-2">Comercial coop.</th>
                  <th className="text-center font-black uppercase tracking-wide px-3 py-2">Montador coop.</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u) => (
                  <tr key={u.id} className="border-t border-slate-100">
                    <td className="px-3 py-2">
                      <span className="font-bold text-dato-800">
                        {u.clientName || u.username}
                      </span>
                      {hecho === u.id && <Check size={13} className="inline ml-1 text-ok-600" />}
                      <div className="text-[10px] text-dato-500">
                        {u.username} · {NOMBRES[plataformaDe(u)]}
                      </div>
                    </td>
                    {['esCooperativistaComercial', 'esCooperativistaMontador'].map((campo) => (
                      <td key={campo} className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={!!u[campo]}
                          disabled={guardando === u.id}
                          onChange={(e) => marcar(u, campo, e.target.checked)}
                          className="w-4 h-4 rounded accent-ok-600 disabled:opacity-40"
                          data-testid={`coop-${campo}-${u.id}`}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
