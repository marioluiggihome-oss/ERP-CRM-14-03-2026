/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL GASTO DE IA, DETRÁS DE UN CANDADO Y SOLO PARA EL MASTER.
 *
 * El master, 14/09/2026: «pon un botón solo para máster para ver estos gastos
 * con un candado y pulsando shift».
 *
 * POR QUÉ UN CANDADO Y NO UN BOTÓN NORMAL: por aquí se ve lo que la casa se
 * gasta en IA y QUIÉN lo gasta. Es la misma clase de dato que el coste y el
 * margen de Rentabilidad, y se protege igual (regla 9): no se bloquea la
 * pantalla, se OCULTAN los importes hasta que alguien hace un gesto
 * deliberado. Así el Estudio 3D se puede enseñar con un cliente delante sin
 * que aparezcan los euros de la casa.
 *
 * EL GESTO ES EL MISMO DEL RESTO DEL ERP —Shift+clic, o mantener pulsado un
 * segundo— y eso no es un detalle: UNA TABLET NO TIENE TECLA SHIFT. Con solo
 * Shift, en la tablet del master el candado no se abriría nunca y el botón
 * parecería roto. Por eso se usa `usePulsacionLarga`, que ya resuelve las dos
 * formas en un solo sitio.
 *
 * Y EL CIERRE DE VERDAD ESTÁ EN EL SERVIDOR: `/api/admin/ai-usage/por-dia` va
 * con `require_master`. Si solo se escondiera el botón, la URL seguiría
 * contestando a cualquiera con sesión — el fallo del motor de render (regla
 * 11), calcado.
 */
import React, { useState, useCallback } from 'react';
import { Lock, Unlock, X, Loader } from 'lucide-react';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', {
  minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const entero = (n) => (Number(n) || 0).toLocaleString('es-ES');
// El audio se factura por MINUTO, así que se enseña en minutos. Un motor que no
// es de voz no trae segundos: ahí va una raya y no un «0 min», que parecería que
// se ha dictado algo y ha salido gratis.
const minutos = (s) => {
  const seg = Number(s) || 0;
  if (!seg) return '—';
  return `${(seg / 60).toLocaleString('es-ES', { maximumFractionDigits: 1 })} min`;
};

export default function ConsumoIADelDia({ esMaster, apiUrl, cabeceras }) {
  const [abierto, setAbierto] = useState(false);
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [diaAbierto, setDiaAbierto] = useState(null);
  /* EL RANGO DE FECHAS (master, 15/09/2026: «que lo pueda calcular por
     fechas»). Antes solo se podían pedir «los últimos N días» contando desde
     hoy, que no sirve ni para cerrar un mes ni para comparar dos semanas.
     Empieza vacío = últimos 30 días, que es lo que se mira el 90 % de las
     veces; en cuanto se toca una fecha, manda el rango. */
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');

  const consultar = useCallback(async (d, h) => {
    setCargando(true); setError(null);
    try {
      const q = (d || h)
        ? `desde=${encodeURIComponent(d || '')}&hasta=${encodeURIComponent(h || '')}`
        : 'dias=30';
      const r = await fetch(`${apiUrl}/api/admin/ai-usage/por-dia?${q}`,
        { headers: cabeceras() });
      if (r.status === 403) { setError('Este consumo es solo del master.'); return; }
      if (!r.ok) { setError(`No se pudo leer el consumo (HTTP ${r.status}).`); return; }
      const j = await r.json();
      setDatos(j && j.success ? j : { dias: [], por_usuario: [], por_modelo: [], por_tipo: {}, total: {} });
    } catch {
      setError('Error de conexión al leer el consumo.');
    } finally { setCargando(false); }
  }, [apiUrl, cabeceras]);

  const abrir = useCallback(() => {
    setAbierto(true);
    if (!datos && !cargando) consultar(desde, hasta);
  }, [datos, cargando, consultar, desde, hasta]);

  const largo = usePulsacionLarga(abrir);

  // Atajos: lo que de verdad se pide es «este mes» o «los últimos 7 días».
  // Tecleando dos fechas a mano en una tablet eso cuesta ocho toques.
  const rangoRapido = (dias) => {
    const f = new Date();
    const fin = f.toISOString().slice(0, 10);
    const ini = dias === 'mes'
      ? `${fin.slice(0, 7)}-01`
      : new Date(f.getTime() - (dias - 1) * 86400000).toISOString().slice(0, 10);
    setDesde(ini); setHasta(fin); consultar(ini, fin);
  };

  // El botón no existe para quien no es master: enseñarlo apagado sería
  // contarle que hay un sitio con los euros de la casa.
  if (!esMaster) return null;

  const dias = (datos && datos.dias) || [];
  const hoy = dias[0];
  const porModelo = (datos && datos.por_modelo) || [];
  const porTipo = (datos && datos.por_tipo) || {};
  const total = (datos && datos.total) || {};
  // Los nombres de los tipos, para no enseñar `otro` a pelo.
  const TIPOS = { render: 'Renders', vision: 'Leer planos y fotos',
                  text: 'Texto', search: 'Búsqueda', otro: 'Otros' };

  return (
    <>
      <button
        type="button"
        {...largo.props}
        onClick={(e) => {
          if (largo.consumir()) return;   // ya lo ha abierto la pulsación larga
          if (e.shiftKey) { abrir(); return; }
          // Un clic suelto NO abre: es un candado, no un botón.
          setError(null);
          setAbierto(false);
          window.alert(`Consumo de IA — ${AYUDA_CANDADO}.`);
        }}
        data-testid="candado-consumo-ia"
        title={`Gasto de IA día a día (solo master). ${AYUDA_CANDADO}`}
        className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-black bg-slate-100 text-slate-500 hover:bg-slate-200">
        {abierto ? <Unlock size={12} /> : <Lock size={12} />}
        <span className="hidden sm:inline">Gasto IA</span>
      </button>

      {abierto && (
        <div className="fixed inset-0 z-[70] bg-black/60 flex items-center justify-center p-3"
          onClick={() => setAbierto(false)}>
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}>
            <div className="p-3 border-b border-slate-200 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-black text-slate-800">Gasto de IA, día a día</h3>
                <p className="text-[11px] text-slate-500">
                  Interno · no sale en nada que vea un cliente
                  {datos && datos.desde ? ` · hay registro desde el ${datos.desde}` : ''}
                </p>
              </div>
              <button onClick={() => setAbierto(false)}
                className="p-1.5 rounded-lg hover:bg-slate-100" title="Cerrar">
                <X size={16} className="text-slate-500" />
              </button>
            </div>

            {/* RANGO DE FECHAS. Los atajos primero, que es lo que se usa. */}
            <div className="p-2 border-b border-slate-200 flex items-center gap-1.5 flex-wrap bg-slate-50">
              {[['Hoy', 1], ['7 días', 7], ['30 días', 30], ['Este mes', 'mes']].map(([rot, n]) => (
                <button key={rot} type="button" onClick={() => rangoRapido(n)}
                  className="px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-100 text-slate-700">
                  {rot}
                </button>
              ))}
              <span className="w-px h-4 bg-slate-200 mx-1" />
              <input type="date" value={desde} max={hasta || undefined}
                onChange={(e) => setDesde(e.target.value)}
                data-testid="gasto-ia-desde"
                className="px-2 py-1 rounded-lg border border-slate-200 text-[11px] font-mono" />
              <span className="text-[11px] text-slate-400">a</span>
              <input type="date" value={hasta} min={desde || undefined}
                onChange={(e) => setHasta(e.target.value)}
                data-testid="gasto-ia-hasta"
                className="px-2 py-1 rounded-lg border border-slate-200 text-[11px] font-mono" />
              <button type="button" onClick={() => consultar(desde, hasta)}
                className="px-2 py-1 rounded-lg text-[11px] font-black bg-accion-600 text-white hover:bg-accion-700">
                Ver
              </button>
              {(desde || hasta) && (
                <button type="button"
                  onClick={() => { setDesde(''); setHasta(''); consultar('', ''); }}
                  className="px-2 py-1 rounded-lg text-[11px] font-bold text-slate-500 hover:bg-slate-100">
                  Quitar filtro
                </button>
              )}
            </div>

            {cargando ? (
              <div className="p-8 text-center text-slate-500">
                <Loader size={22} className="animate-spin mx-auto mb-2" /> Leyendo el consumo…
              </div>
            ) : error ? (
              <div className="p-6 text-center text-sm font-bold text-error-600">{error}</div>
            ) : dias.length === 0 ? (
              <div className="p-6 text-sm text-slate-500">
                Todavía no hay días registrados. El contador diario empieza con la
                primera llamada a la IA desde el 14/09/2026; lo anterior solo está
                por meses, en el panel Master.
              </div>
            ) : (
              <div className="overflow-auto">
                {/* EL TOTAL ES DEL RANGO ELEGIDO, no del último día: si
                    pones «este mes» y arriba siguiera el número de hoy, la
                    cifra grande de la pantalla contestaría a otra pregunta. */}
                <div className="p-3 bg-slate-50 border-b border-slate-200 flex gap-4 flex-wrap">
                  <div>
                    <div className="text-[10px] font-black uppercase text-slate-400">
                      {desde || hasta
                        ? `Del ${desde || '…'} al ${hasta || '…'}`
                        : `Últimos ${total.dias || 0} día(s) con gasto`}
                    </div>
                    <div className="text-lg font-black text-dato-900" data-testid="gasto-ia-total">
                      {eur(total.cost_eur)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-black uppercase text-slate-400">Llamadas</div>
                    <div className="text-lg font-black text-slate-700">{entero(total.llamadas)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-black uppercase text-slate-400">Imágenes</div>
                    <div className="text-lg font-black text-slate-700">{entero(total.imagenes)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-black uppercase text-slate-400">Tokens</div>
                    <div className="text-lg font-black text-slate-700">
                      {entero((total.tokens_in || 0) + (total.tokens_out || 0))}
                    </div>
                  </div>
                  {hoy && !desde && !hasta && (
                    <div className="ml-auto text-right">
                      <div className="text-[10px] font-black uppercase text-slate-400">Hoy ({hoy.day})</div>
                      <div className="text-lg font-black text-dato-900">{eur(hoy.cost_eur)}</div>
                    </div>
                  )}
                </div>

                {/* ─── POR TIPO DE IA (master, 15/09: «q diga el gasto por
                    tipos de IAS»). Dos cortes, porque contestan cosas
                    distintas: QUÉ se le ha pedido a la IA (renders, leer
                    planos…) y CON QUÉ se ha pintado, que es de donde sale el
                    euro. */}
                {porModelo.length > 0 && (
                  <div className="p-3 border-b border-slate-200">
                    <div className="text-[10px] font-black uppercase text-slate-400 mb-1">
                      Por tipo de trabajo
                    </div>
                    <div className="flex gap-2 flex-wrap mb-3">
                      {Object.entries(porTipo).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
                        <span key={k} className="px-2 py-1 rounded-lg bg-slate-100 text-[11px] font-bold text-slate-700">
                          {TIPOS[k] || k} <b className="font-mono">{entero(v)}</b>
                        </span>
                      ))}
                    </div>
                    <div className="text-[10px] font-black uppercase text-slate-400 mb-1">
                      Por motor · de aquí sale el coste
                    </div>
                    <table className="w-full text-xs" data-testid="gasto-ia-por-modelo">
                      <thead className="bg-slate-100 text-slate-500">
                        <tr>
                          <th className="text-left px-2 py-1 font-black uppercase">Motor</th>
                          <th className="text-right px-2 py-1 font-black uppercase">Llam.</th>
                          <th className="text-right px-2 py-1 font-black uppercase">Imág.</th>
                          <th className="text-right px-2 py-1 font-black uppercase">Audio</th>
                          <th className="text-right px-2 py-1 font-black uppercase">Tokens</th>
                          <th className="text-right px-2 py-1 font-black uppercase">Coste</th>
                        </tr>
                      </thead>
                      <tbody className="font-mono">
                        {porModelo.map(m => (
                          <tr key={m.modelo} className="border-b border-slate-100">
                            <td className="px-2 py-1 font-sans font-bold text-slate-700">
                              {m.modelo}
                              {!m.tarifa_conocida && (
                                <span className="ml-1 text-[9px] font-black text-aviso-600"
                                  title="Este motor no está en la tabla de tarifas: el coste va con el precio por defecto y NO es fiable.">
                                  tarifa sin confirmar
                                </span>
                              )}
                            </td>
                            <td className="px-2 py-1 text-right text-slate-600">{entero(m.llamadas)}</td>
                            <td className="px-2 py-1 text-right text-slate-600">{entero(m.imagenes)}</td>
                            {/* El dictado del servidor se factura por MINUTO, no por
                                tokens: sin esta columna Whisper saldría con todo a cero
                                y un coste que no se podría explicar con nada de la fila. */}
                            <td className="px-2 py-1 text-right text-slate-600">{minutos(m.segundos)}</td>
                            <td className="px-2 py-1 text-right text-slate-600">
                              {entero((m.tokens_in || 0) + (m.tokens_out || 0))}
                            </td>
                            <td className="px-2 py-1 text-right font-black text-dato-900">{eur(m.cost_eur)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="mt-1 text-[10px] text-slate-400">
                      Lo que se guarda es el MOTOR, no el botón: IA 0 e IA 7 piden el
                      mismo, así que no se puede repartir por botón sin inventárselo.
                    </p>
                  </div>
                )}
                <table className="w-full text-xs">
                  <thead className="bg-slate-100 text-slate-500 sticky top-0">
                    <tr>
                      <th className="text-left px-2 py-1.5 font-black uppercase">Día</th>
                      <th className="text-right px-2 py-1.5 font-black uppercase">Llam.</th>
                      <th className="text-right px-2 py-1.5 font-black uppercase">Imág.</th>
                      <th className="text-right px-2 py-1.5 font-black uppercase">Tokens</th>
                      <th className="text-right px-2 py-1.5 font-black uppercase">Coste</th>
                      <th className="text-left px-2 py-1.5 font-black uppercase">Quién</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {dias.map(d => {
                      const gente = Object.entries(d.by_user || {}).sort((a, b) => b[1] - a[1]);
                      const todo = diaAbierto === d.day;
                      return (
                        <tr key={d.day} className="border-b border-slate-100">
                          <td className="px-2 py-1.5 font-bold text-slate-700">{d.day}</td>
                          <td className="px-2 py-1.5 text-right font-black text-slate-800">{entero(d.total)}</td>
                          <td className="px-2 py-1.5 text-right text-slate-600">{entero(d.images)}</td>
                          <td className="px-2 py-1.5 text-right text-slate-600"
                            title={`${entero(d.tokens_in)} entrada · ${entero(d.tokens_out)} salida`}>
                            {entero((d.tokens_in || 0) + (d.tokens_out || 0))}
                          </td>
                          <td className="px-2 py-1.5 text-right font-black text-dato-900">{eur(d.cost_eur)}</td>
                          <td className="px-2 py-1.5 font-sans text-slate-600">
                            {gente.length === 0 ? <span className="text-slate-300">·</span> : (
                              <>
                                {(todo ? gente : gente.slice(0, 2)).map(([q, v]) => (
                                  <span key={q} className="inline-block mr-2 whitespace-nowrap">
                                    {q} <b className="font-mono">{entero(v)}</b>
                                  </span>
                                ))}
                                {gente.length > 2 && (
                                  <button type="button"
                                    onClick={() => setDiaAbierto(todo ? null : d.day)}
                                    className="text-accion-600 font-bold underline">
                                    {todo ? 'ver menos' : `+${gente.length - 2}`}
                                  </button>
                                )}
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
