/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Users, Wrench, Briefcase, AlertTriangle, Check, Loader } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const fecha = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('es-ES');
};

/**
 * SOCIOS COOPERATIVISTAS: QUIÉN COBRA CADA PEDIDO. SOLO EL MASTER.
 *
 * Sin esta pantalla el resto del área no sirve de nada. Un pedido servido y
 * cobrado al que nadie le ha puesto comercial ni montador NO da ningún error:
 * simplemente no aparece en la nómina de nadie, y de eso no se entera nunca
 * quien tenía que cobrar. Por eso lo primero que se ve son los pedidos SIN
 * ASIGNAR, y por eso se cuentan arriba.
 *
 * NO SE ENSEÑA EL IMPORTE del pedido. El master podría verlo, pero para decidir
 * quién montó una cocina no hace falta, y cuanto menos dinero viaje por
 * pantallas nuevas, menos sitios hay por los que se pueda escapar (CLAUDE.md,
 * reglas 8b y 9). Lo que sí se enseña son los MUEBLES que cuentan para la
 * comisión, que no son los del pedido entero: puertas, costados y servicios no
 * incentivan.
 */
const Selector = ({ valor, opciones, onChange, vacio, guardando }) => (
  <select
    value={valor || ''}
    disabled={guardando}
    onChange={(e) => onChange(e.target.value)}
    className={`w-full px-2 py-1 rounded-lg border text-xs font-bold bg-white disabled:opacity-50 ${
      valor ? 'border-slate-300 text-slate-800' : 'border-aviso-400 text-aviso-700'}`}
  >
    <option value="">{vacio}</option>
    {opciones.map((o) => (
      <option key={o.id} value={o.id}>{o.nombre || o.id}</option>
    ))}
  </select>
);

export default function SociosCooperativistas() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState('');
  const [guardado, setGuardado] = useState('');
  const [aplicando, setAplicando] = useState(false);

  const cabeceras = useCallback(() => {
    const t = localStorage.getItem('token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const r = await fetch(`${API_URL}/api/cooperativistas/pedidos`, { headers: cabeceras() });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'No se pudieron cargar los pedidos.'); return; }
      setDatos(d);
      setError('');
    } catch {
      setError('No se pudo conectar con el servidor.');
    } finally {
      setCargando(false);
    }
  }, [cabeceras]);

  useEffect(() => { cargar(); }, [cargar]);

  const asignar = async (pedidoId, clave, valor) => {
    setGuardando(pedidoId);
    try {
      const r = await fetch(`${API_URL}/api/cooperativistas/asignar`, {
        method: 'POST',
        headers: { ...cabeceras(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ pedidoId, [clave]: valor }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'No se pudo asignar.'); return; }
      // Se recarga en vez de tocar el estado a mano: quien manda es el
      // servidor, y así el recuento de «sin asignar» no puede mentir.
      await cargar();
      setGuardado(pedidoId);
      setTimeout(() => setGuardado(''), 2000);
    } catch {
      setError('No se pudo conectar con el servidor.');
    } finally {
      setGuardando('');
    }
  };

  const aplicarSugerencias = async () => {
    setAplicando(true);
    try {
      const r = await fetch(`${API_URL}/api/cooperativistas/aplicar-sugerencias`, {
        method: 'POST', headers: cabeceras(),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'No se pudieron aplicar.'); return; }
      await cargar();
    } catch {
      setError('No se pudo conectar con el servidor.');
    } finally {
      setAplicando(false);
    }
  };

  if (cargando && !datos) {
    return (
      <div className="h-full flex items-center justify-center text-dato-500">
        <Loader className="animate-spin mr-2" size={18} /> Cargando…
      </div>
    );
  }

  if (error && !datos) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <AlertTriangle className="mx-auto mb-2 text-error-600" size={28} />
          <p className="text-sm font-bold text-dato-700">{error}</p>
        </div>
      </div>
    );
  }

  const socios = datos?.socios || { comerciales: [], montadores: [] };
  const pedidos = datos?.pedidos || [];
  const sinAsignar = datos?.sinAsignar || 0;
  const haySocios = socios.comerciales.length + socios.montadores.length > 0;

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
        <h1 className="text-xl font-black text-dato-800 tracking-tight flex items-center gap-2">
          <Users size={20} /> Socios cooperativistas
        </h1>
        <p className="text-xs text-dato-500 mt-1 mb-5">
          Quién vendió y quién montó cada pedido. Es lo que decide quién cobra,
          así que solo lo tocas tú.
        </p>

        {error && (
          <div className="mb-4 rounded-xl border border-error-300 bg-error-50 px-3 py-2 text-xs font-bold text-error-700">
            {error}
          </div>
        )}

        {/* Los socios que hay */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 text-accion-700 mb-2">
              <Briefcase size={15} />
              <span className="text-[11px] font-black uppercase tracking-wide">
                Comerciales ({socios.comerciales.length})
              </span>
            </div>
            {socios.comerciales.length === 0
              ? <p className="text-[11px] text-dato-500">Ninguno marcado todavía.</p>
              : socios.comerciales.map((s) => (
                  <div key={s.id} className="text-xs font-bold text-dato-700">{s.nombre || s.id}</div>
                ))}
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 text-accion-700 mb-2">
              <Wrench size={15} />
              <span className="text-[11px] font-black uppercase tracking-wide">
                Montadores ({socios.montadores.length})
              </span>
            </div>
            {socios.montadores.length === 0
              ? <p className="text-[11px] text-dato-500">Ninguno marcado todavía.</p>
              : socios.montadores.map((s) => (
                  <div key={s.id} className="text-xs font-bold text-dato-700 flex justify-between gap-2">
                    <span>{s.nombre || s.id}</span>
                    <span className="text-dato-500 tabular-nums">{s.manoObraPorMueble} € / mueble</span>
                  </div>
                ))}
          </div>
        </div>

        {!haySocios && (
          <div className="mb-5 rounded-xl border border-aviso-300 bg-aviso-50 px-3 py-2 text-xs font-bold text-aviso-800">
            Todavía no has marcado a ningún socio. Se marca en la ficha de cada
            usuario, en el panel Master: «Comercial cooperativista» o «Montador
            cooperativista». Hasta entonces no hay a quién asignarle un pedido.
          </div>
        )}

        {(datos?.sugerencias || 0) > 0 && (
          <div className="mb-3 rounded-xl border border-accion-300 bg-accion-50 px-3 py-2 flex items-center justify-between gap-3 flex-wrap">
            <span className="text-xs font-bold text-accion-800">
              La agenda de montajes sabe quién montó {datos.sugerencias} pedido
              {datos.sugerencias === 1 ? '' : 's'} que no tiene{datos.sugerencias === 1 ? '' : 'n'} montador.
              Solo se proponen socios: los montadores externos no entran.
            </span>
            <button
              onClick={aplicarSugerencias}
              disabled={aplicando}
              className="px-3 py-1.5 rounded-lg bg-accion-600 text-white text-[11px] font-black uppercase tracking-widest disabled:opacity-40 hover:bg-accion-700 transition-colors"
              data-testid="aplicar-sugerencias-btn"
            >
              {aplicando ? 'Aplicando…' : 'Poner los de la agenda'}
            </button>
          </div>
        )}

        {sinAsignar > 0 && (
          <div className="mb-3 flex items-center gap-2 text-xs font-black text-aviso-800">
            <AlertTriangle size={15} />
            {sinAsignar === 1
              ? '1 pedido sin asignar del todo: no le paga a nadie.'
              : `${sinAsignar} pedidos sin asignar del todo: no le pagan a nadie.`}
          </div>
        )}

        {/* Los pedidos */}
        {pedidos.length === 0 ? (
          <p className="text-sm text-dato-500">Todavía no hay pedidos.</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-dato-500">
                <tr>
                  <th className="text-left font-black uppercase tracking-wide px-3 py-2">Pedido</th>
                  <th className="text-right font-black uppercase tracking-wide px-3 py-2">Muebles</th>
                  <th className="text-left font-black uppercase tracking-wide px-3 py-2">Comercial</th>
                  <th className="text-left font-black uppercase tracking-wide px-3 py-2">Montador</th>
                </tr>
              </thead>
              <tbody>
                {pedidos.map((p) => (
                  <tr key={p.pedidoId}
                      className={`border-t border-slate-100 ${p.sinAsignar ? 'bg-aviso-50/40' : ''}`}>
                    <td className="px-3 py-2 align-top">
                      <div className="font-bold text-dato-800">
                        {p.cliente || 'Sin cliente'}
                        {guardado === p.pedidoId && (
                          <Check size={13} className="inline ml-1 text-ok-600" />
                        )}
                      </div>
                      <div className="text-[10px] text-dato-500">
                        {p.referencia ? `${p.referencia} · ` : ''}{fecha(p.fecha)}
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top text-right tabular-nums font-bold text-dato-700">
                      {p.sinDesglose
                        ? <span title="Este pedido no trae sus líneas, así que no se puede saber cuántos muebles cuentan para la comisión."
                                className="text-aviso-700">?</span>
                        : p.muebles}
                    </td>
                    <td className="px-3 py-2 align-top w-48">
                      <Selector
                        valor={p.comercialUserId}
                        opciones={socios.comerciales}
                        vacio="— sin asignar —"
                        guardando={guardando === p.pedidoId}
                        onChange={(v) => asignar(p.pedidoId, 'comercialUserId', v)}
                      />
                    </td>
                    <td className="px-3 py-2 align-top w-48">
                      <Selector
                        valor={p.montadorUserId}
                        opciones={socios.montadores}
                        vacio="— sin asignar —"
                        guardando={guardando === p.pedidoId}
                        onChange={(v) => asignar(p.pedidoId, 'montadorUserId', v)}
                      />
                      {p.sugerencia && (
                        <button
                          onClick={() => asignar(p.pedidoId, 'montadorUserId', p.sugerencia.montadorUserId)}
                          disabled={guardando === p.pedidoId}
                          className="mt-1 text-[10px] font-bold text-accion-700 hover:underline text-left disabled:opacity-40"
                          title={`La agenda dice que lo montó ${p.sugerencia.porque}`}
                        >
                          agenda: {p.sugerencia.nombre} →
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-[10px] text-dato-400 mt-3">
          Los muebles son los que cuentan para la comisión, no las líneas del
          pedido: puertas, costados, regletas y los servicios que añades a mano
          no incentivan. Un «?» es un pedido sin desglose, que no paga hasta que
          se arregle.
        </p>
      </div>
    </div>
  );
}
