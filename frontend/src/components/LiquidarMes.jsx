/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Wallet, AlertTriangle, Lock, Loader, Check } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', {
  minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

/** «2026-08» → «agosto de 2026». Se deriva, no se escribe a mano. */
const nombreDelPeriodo = (p) => {
  const m = /^(\d{4})-(\d{2})$/.exec(p || '');
  if (!m) return p || '';
  const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
                 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  return `${meses[Number(m[2]) - 1] || m[2]} de ${m[1]}`;
};

/** Los últimos doce meses, del más reciente al más antiguo. */
const ultimosMeses = (n = 12) => {
  const hoy = new Date();
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
};

/**
 * CERRAR EL MES: LO QUE SE LE PAGA A CADA COOPERATIVISTA.
 *
 * Lo que hace esta pantalla no se deshace: al cerrar, cada pedido queda marcado
 * como liquidado y con su importe CONGELADO dentro. Desde ese momento cambiar
 * la mano de obra de un montador ya no mueve lo que se le pagó (CLAUDE.md,
 * regla 17). Por eso se enseña el desglose completo ANTES de pulsar y se pide
 * confirmación: es la única pantalla del ERP que compromete dinero de verdad.
 *
 * Pulsar dos veces no paga dos veces — el servidor se salta lo ya liquidado—,
 * pero el botón igualmente se bloquea mientras trabaja: que la barrera esté en
 * el servidor no es excusa para poner una trampa en la pantalla.
 */
export default function LiquidarMes() {
  const meses = useMemo(() => ultimosMeses(12), []);
  const [socios, setSocios] = useState({ comerciales: [], montadores: [] });
  const [rol, setRol] = useState('todos');
  const [usuario, setUsuario] = useState('');
  const [periodo, setPeriodo] = useState(meses[0]);
  const [detalle, setDetalle] = useState(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const [liquidando, setLiquidando] = useState(false);
  const [hecho, setHecho] = useState(null);

  const cabeceras = useCallback(() => {
    const t = localStorage.getItem('token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_URL}/api/cooperativistas/socios`, { headers: cabeceras() });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) { setError(d.detail || 'No se pudo cargar la lista de socios.'); return; }
        setSocios(d.socios || { comerciales: [], montadores: [] });
      } catch {
        setError('No se pudo conectar con el servidor.');
      }
    })();
  }, [cabeceras]);

  // La lista de a quién liquidar, según el rol elegido.
  const candidatos = useMemo(() => {
    const c = socios.comerciales.map((s) => ({ ...s, rol: 'comercial' }));
    const m = socios.montadores.map((s) => ({ ...s, rol: 'montador' }));
    if (rol === 'comercial') return c;
    if (rol === 'montador') return m;
    return [...c, ...m];
  }, [socios, rol]);

  // Si el filtro de rol deja fuera al elegido, se deselecciona: mejor vacío que
  // enseñando la liquidación de alguien que ya no está en la lista.
  useEffect(() => {
    if (usuario && !candidatos.some((c) => c.id === usuario)) setUsuario('');
  }, [candidatos, usuario]);

  const ver = useCallback(async () => {
    if (!usuario || !periodo) { setDetalle(null); return; }
    setCargando(true); setHecho(null);
    try {
      const r = await fetch(
        `${API_URL}/api/cooperativistas/liquidacion?periodo=${encodeURIComponent(periodo)}&usuario=${encodeURIComponent(usuario)}`,
        { headers: cabeceras() });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'No se pudo cargar la liquidación.'); setDetalle(null); return; }
      setDetalle(d.liquidacion || null);
      setError('');
    } catch {
      setError('No se pudo conectar con el servidor.');
    } finally {
      setCargando(false);
    }
  }, [usuario, periodo, cabeceras]);

  useEffect(() => { ver(); }, [ver]);

  const liquidar = async () => {
    const quien = candidatos.find((c) => c.id === usuario);
    const aviso = `Vas a cerrar ${nombreDelPeriodo(periodo)} de ${quien?.nombre || usuario}.\n\n`
      + `Se pagan ${eur(detalle?.euros)} y los importes quedan congelados: a partir de `
      + `ahora no cambian aunque cambies una tarifa.\n\n¿Seguimos?`;
    // eslint-disable-next-line no-alert
    if (!window.confirm(aviso)) return;
    setLiquidando(true);
    try {
      const r = await fetch(`${API_URL}/api/cooperativistas/liquidar`, {
        method: 'POST',
        headers: { ...cabeceras(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario, periodo }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'No se pudo cerrar el mes.'); return; }
      setHecho(d);
      await ver();
    } catch {
      setError('No se pudo conectar con el servidor.');
    } finally {
      setLiquidando(false);
    }
  };

  const lineas = detalle?.lineas || [];
  const pendientes = lineas.filter((l) => l.estado === 'consolidada');
  const anomalias = lineas.filter((l) => l.anomalia);

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-8 py-6">
        <h1 className="text-xl font-black text-dato-800 tracking-tight flex items-center gap-2">
          <Wallet size={20} /> Liquidar el mes
        </h1>
        <p className="text-xs text-dato-500 mt-1 mb-5">
          Lo que se le paga a cada cooperativista. Al cerrar, los importes quedan
          congelados y no vuelven a entrar en ninguna liquidación.
        </p>

        {error && (
          <div className="mb-4 rounded-xl border border-error-300 bg-error-50 px-3 py-2 text-xs font-bold text-error-700">
            {error}
          </div>
        )}

        {/* Filtros */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
          <label className="block">
            <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Rol</span>
            <select
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800 bg-white"
              data-testid="liquidar-filtro-rol"
            >
              <option value="todos">Todos</option>
              <option value="comercial">Comerciales</option>
              <option value="montador">Montadores</option>
            </select>
          </label>
          <label className="block">
            <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Cooperativista</span>
            <select
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800 bg-white"
              data-testid="liquidar-filtro-usuario"
            >
              <option value="">— elige a quién —</option>
              {candidatos.map((c) => (
                <option key={`${c.rol}-${c.id}`} value={c.id}>
                  {c.nombre || c.id} · {c.rol}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-[10px] font-black uppercase tracking-widest text-dato-500">Mes</span>
            <select
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-dato-800 bg-white"
              data-testid="liquidar-filtro-periodo"
            >
              {meses.map((m) => (
                <option key={m} value={m}>{nombreDelPeriodo(m)}</option>
              ))}
            </select>
          </label>
        </div>

        {candidatos.length === 0 && (
          <div className="rounded-xl border border-aviso-300 bg-aviso-50 px-3 py-2 text-xs font-bold text-aviso-800">
            No hay socios marcados con ese rol. Se marcan en la ficha del usuario,
            en el panel Master.
          </div>
        )}

        {!usuario && candidatos.length > 0 && (
          <p className="text-sm text-dato-500">Elige a quién quieres liquidar.</p>
        )}

        {cargando && (
          <div className="flex items-center gap-2 text-dato-500 text-sm">
            <Loader className="animate-spin" size={16} /> Calculando…
          </div>
        )}

        {hecho && (
          <div className="mb-4 rounded-xl border border-ok-300 bg-ok-50 px-3 py-2 text-xs font-bold text-ok-800 flex items-center gap-2">
            <Check size={15} />
            Cerrado {nombreDelPeriodo(hecho.periodo)}: {eur(hecho.total)} en{' '}
            {hecho.pedidos?.length || 0} pedido{(hecho.pedidos?.length || 0) === 1 ? '' : 's'}.
            {hecho.yaLiquidados > 0 && ` (${hecho.yaLiquidados} ya estaban liquidados y no se han vuelto a pagar.)`}
          </div>
        )}

        {usuario && !cargando && detalle && (
          <>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 mb-4">
              <div className="text-[11px] font-black uppercase tracking-wide text-dato-500">
                A pagar en {nombreDelPeriodo(periodo)}
              </div>
              <div className="text-3xl font-black text-dato-900 tabular-nums leading-tight">
                {eur(detalle.euros)}
              </div>
              <div className="text-[11px] text-dato-500 mt-1">
                {pendientes.length} pedido{pendientes.length === 1 ? '' : 's'} servido
                {pendientes.length === 1 ? '' : 's'} y cobrado{pendientes.length === 1 ? '' : 's'}
              </div>
              <button
                onClick={liquidar}
                disabled={liquidando || (detalle.euros || 0) <= 0}
                className="mt-4 px-4 py-2 rounded-xl bg-master-600 text-white text-xs font-black uppercase tracking-widest disabled:opacity-40 disabled:cursor-not-allowed hover:bg-master-700 transition-colors flex items-center gap-2"
                data-testid="liquidar-cerrar-btn"
              >
                <Lock size={14} />
                {liquidando ? 'Cerrando…' : 'Cerrar el mes y pagar'}
              </button>
              <p className="text-[10px] text-dato-400 mt-2">
                No se deshace: los importes quedan congelados en cada pedido.
              </p>
            </div>

            {anomalias.length > 0 && (
              <div className="mb-4 rounded-xl border border-aviso-300 bg-aviso-50 px-3 py-2 text-xs font-bold text-aviso-800 flex items-start gap-2">
                <AlertTriangle size={15} className="mt-0.5 shrink-0" />
                <span>
                  {anomalias.length} pedido{anomalias.length === 1 ? '' : 's'} salió del
                  almacén sin estar cobrado del todo. No se paga{anomalias.length === 1 ? '' : 'n'}
                  {' '}hasta que el cobro cuadre.
                </span>
              </div>
            )}

            {lineas.length === 0 ? (
              <p className="text-sm text-dato-500">
                No hay nada que liquidar en {nombreDelPeriodo(periodo)}.
              </p>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-dato-500">
                    <tr>
                      <th className="text-left font-black uppercase tracking-wide px-3 py-2">Pedido</th>
                      <th className="text-right font-black uppercase tracking-wide px-3 py-2">Muebles</th>
                      <th className="text-right font-black uppercase tracking-wide px-3 py-2">Por mueble</th>
                      <th className="text-right font-black uppercase tracking-wide px-3 py-2">Euros</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineas.map((l) => (
                      <tr key={l.pedidoId} className="border-t border-slate-100">
                        <td className="px-3 py-2">
                          <span className="font-bold text-dato-800">{l.pedidoId}</span>
                          {l.anomalia && (
                            <AlertTriangle size={12} className="inline ml-1 text-aviso-600" />
                          )}
                          {l.tramo && <div className="text-[10px] text-dato-500">{l.tramo}</div>}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums">{l.muebles}</td>
                        <td className="px-3 py-2 text-right tabular-nums">{eur(l.porMueble)}</td>
                        <td className="px-3 py-2 text-right tabular-nums font-black text-dato-900">
                          {eur(l.euros)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
