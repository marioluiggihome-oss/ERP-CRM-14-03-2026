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
