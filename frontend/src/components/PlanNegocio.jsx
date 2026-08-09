/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * PlanNegocio — EL PLAN DE NEGOCIO DE LA FÁBRICA. SOLO EL MASTER.
 *
 * Se rellena como una hoja de cálculo y calcula solo: se toca el precio del
 * casco y cambian el margen, el punto de equilibrio y el EBITDA.
 *
 * LAS DOS COSAS QUE HACEN QUE ESTO SIRVA
 * --------------------------------------
 * 1. LO QUE NO SE SABE SE VE. Una casilla sin rellenar queda AMARILLA y lo que
 *    depende de ella dice «falta dato». Nunca un cero: un cero parece un
 *    resultado, y un plan con ceros de relleno es el documento más peligroso
 *    que puede salir de aquí, porque se enseña a un banco.
 *
 * 2. LAS CUENTAS LAS HACE EL SERVIDOR. Aquí no se calcula nada. Están en
 *    `services/plan_negocio.py`, que es cálculo puro y tiene sus candados: así
 *    lo que decide el plan se puede probar de verdad, y no depende de que la
 *    pantalla esté abierta.
 *
 * El botón de Excel baja el mismo plan CON FÓRMULAS, para poder seguir
 * tanteando fuera del ERP.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Calculator, Save, Download, Loader, AlertTriangle, TrendingUp, Factory,
  RefreshCw, CheckCircle2, Lock,
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const auth = () => ({ Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

const MATERIALES = [
  ['casco', 'Casco (compra)'], ['bisagras', 'Bisagras'], ['guias', 'Guías'],
  ['patasZocalo', 'Patas y zócalo'], ['otrosHerrajes', 'Otros herrajes'],
  ['componentes', 'Componentes'], ['embalaje', 'Embalaje'], ['otrosDirectos', 'Otros directos'],
];
const B2C = [
  ['comisionComercial', 'Comisión comercial'], ['montaje', 'Montaje en casa'],
  ['transporte', 'Transporte'], ['postventa', 'Postventa / repasos'],
];

const eur = (n, dec = 2) => (n === null || n === undefined)
  ? null
  : Number(n).toLocaleString('es-ES', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + ' €';
const num = (n) => (n === null || n === undefined) ? null : Number(n).toLocaleString('es-ES');
const pct = (n) => (n === null || n === undefined) ? null : (n * 100).toFixed(1) + ' %';

/** Un resultado calculado. Si no se sabe, LO DICE — no pone un cero. */
const Dato = ({ label, valor, destacado, nota }) => (
  <div className={`rounded-xl border px-3 py-2 ${destacado ? 'bg-emerald-50 border-emerald-300' : 'bg-white border-slate-200'}`}>
    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">{label}</p>
    {valor === null || valor === undefined ? (
      <p className="text-sm font-bold text-amber-600">falta dato</p>
    ) : (
      <p className={`font-black ${destacado ? 'text-lg text-emerald-700' : 'text-sm text-slate-800'}`}>{valor}</p>
    )}
    {nota && <p className="text-[10px] text-slate-400 mt-0.5">{nota}</p>}
  </div>
);

/** Una casilla que rellena el master. Amarilla mientras esté vacía. */
const Casilla = ({ valor, onChange, ancho = 'w-24', paso = '0.01', titulo }) => {
  const vacia = valor === null || valor === undefined || valor === '';
  return (
    <input
      type="number" step={paso} inputMode="decimal" title={titulo}
      value={vacia ? '' : valor}
      onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
      className={`${ancho} px-2 py-1 rounded-lg border text-sm text-right font-semibold outline-none focus:border-indigo-400
        ${vacia ? 'bg-amber-100 border-amber-300 text-amber-800' : 'bg-white border-slate-300 text-slate-800'}`}
    />
  );
};

export default function PlanNegocio({ state }) {
  const [datos, setDatos] = useState(null);
  const [res, setRes] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [guardado, setGuardado] = useState(false);
  const [error, setError] = useState('');
  const [pestana, setPestana] = useState('coste'); // coste | precios | estructura | resultado
  // Cómo se da el coste del material: UN número por mueble (lo normal al
  // empezar) o el desglose en ocho partidas (para saber dónde está el coste
  // cuando haya que apretar al proveedor). Empieza por lo sencillo.
  const [modoCoste, setModoCoste] = useState('mueble'); // mueble | desglose

  const u = state?.currentUser;
  const esMaster = !!(u?.isAdmin || u?.isPrimaryAdmin || u?.isMaster);

  useEffect(() => {
    if (!esMaster) { setCargando(false); return; }
    (async () => {
      try {
        const r = await fetch(`${API_URL}/api/plan-negocio`, { headers: auth() });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || 'No se pudo cargar el plan.');
        setDatos(d.datos); setRes(d.resultado);
      } catch (e) { setError(e.message); }
      finally { setCargando(false); }
    })();
  }, [esMaster]);

  // Recalcular SIN guardar: un plan se hace tanteando, y obligar a guardar cada
  // prueba acaba ensuciando el plan bueno con pruebas a medias.
  const recalcular = useCallback(async (siguientes) => {
    try {
      const r = await fetch(`${API_URL}/api/plan-negocio/calcular`, {
        method: 'POST', headers: auth(), body: JSON.stringify(siguientes),
      });
      const d = await r.json();
      if (r.ok) setRes(d.resultado);
    } catch { /* si falla la red, se sigue editando: se recalcula al guardar */ }
  }, []);

  const tocar = useCallback((cambio) => {
    setDatos(prev => {
      const sig = typeof cambio === 'function' ? cambio(prev) : { ...prev, ...cambio };
      setGuardado(false);
      recalcular(sig);
      return sig;
    });
  }, [recalcular]);

  const guardar = async () => {
    setGuardando(true); setError('');
    try {
      const r = await fetch(`${API_URL}/api/plan-negocio`, {
        method: 'PUT', headers: auth(), body: JSON.stringify(datos),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'No se pudo guardar.');
      setRes(d.resultado); setGuardado(true);
      setTimeout(() => setGuardado(false), 2500);
    } catch (e) { setError(e.message); }
    finally { setGuardando(false); }
  };

  const bajarExcel = async () => {
    try {
      const r = await fetch(`${API_URL}/api/plan-negocio/excel`, { headers: auth() });
      if (!r.ok) throw new Error('No se pudo generar el Excel.');
      const blob = await r.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'plan_negocio.xlsx';
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) { setError(e.message); }
  };

  const refs = datos?.referencias || [];
  const cap = res?.capacidad || {};

  const cambiarRef = (i, clave, valor) => tocar(prev => ({
    ...prev,
    referencias: prev.referencias.map((r, j) => j === i ? { ...r, [clave]: valor } : r),
  }));

  const faltan = res?.faltan || [];
  const listo = useMemo(() => faltan.length === 0, [faltan]);

  if (!esMaster) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 p-8">
        <div className="max-w-md text-center">
          <Lock className="mx-auto text-slate-300" size={40} />
          <p className="mt-3 font-black text-slate-700">El plan de negocio es solo del master.</p>
          <p className="text-sm text-slate-500 mt-1">
            Lleva el coste de compra de los cascos, el descuento del proveedor y el margen por canal.
          </p>
        </div>
      </div>
    );
  }

  if (cargando) {
    return <div className="h-full flex items-center justify-center text-slate-400 gap-2">
      <Loader className="animate-spin" size={20} /> Cargando el plan…
    </div>;
  }

  return (
    <div className="h-full flex flex-col bg-slate-50 overflow-y-auto p-4 sm:p-6 pb-24">
      <div className="hueco-logo rounded-2xl bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-600 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="text-base sm:text-lg font-black flex items-center gap-2">
          <Calculator size={18} /> Plan de negocio
        </h1>
        <span className="text-[10px] font-black uppercase tracking-widest bg-white/20 px-2 py-0.5 rounded">Solo master</span>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={bajarExcel}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-xs font-bold">
            <Download size={14} /> Excel
          </button>
          <button onClick={guardar} disabled={guardando}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-emerald-700 rounded-lg text-xs font-black disabled:opacity-50">
            {guardando ? <Loader size={14} className="animate-spin" /> : guardado ? <CheckCircle2 size={14} /> : <Save size={14} />}
            {guardado ? 'Guardado' : 'Guardar'}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm font-bold text-rose-600 flex items-center gap-1"><AlertTriangle size={14} /> {error}</p>}

      {/* Lo primero que se ve: qué sale y qué falta */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
        <Dato label="Capacidad" valor={num(cap.capacidadAnual)} nota="muebles/año · es un techo" />
        <Dato label="Coste directo medio" valor={eur(res?.costeDirectoMedio)} />
        <Dato label="Margen medio / mueble" valor={eur(res?.margenMedioPonderado)} destacado />
        <Dato label="Punto de equilibrio" valor={num(res?.puntoEquilibrio)} destacado
              nota={res?.parteDeLaCapacidad != null ? `${pct(res.parteDeLaCapacidad)} de la capacidad` : 'muebles/año'} />
      </div>

      {res?.sostenible === false && (
        <div className="mb-4 rounded-xl bg-rose-50 border-2 border-rose-300 px-4 py-3">
          <p className="font-black text-rose-800 flex items-center gap-2"><AlertTriangle size={16} /> Así no sale.</p>
          <p className="text-sm text-rose-700 mt-1">
            Hay que vender {pct(res.parteDeLaCapacidad)} de lo que la fábrica puede hacer solo para cubrir la estructura.
            No es cuestión de apretar: hay que bajar coste o subir precio.
          </p>
        </div>
      )}

      {faltan.length > 0 && (
        <div className="mb-4 rounded-xl bg-amber-50 border border-amber-300 px-4 py-3">
          <p className="font-black text-amber-800 text-sm">Falta esto para poder cerrar el plan</p>
          <ul className="mt-1.5 space-y-1">
            {faltan.map((f, i) => (
              <li key={i} className="text-[12px] text-amber-900">
                <b>{f.que}</b> — <span className="text-amber-700">{f.porque}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-1 bg-white rounded-xl p-1 border border-slate-200 w-fit mb-3 flex-wrap">
        {[['coste', 'Coste por mueble'], ['precios', 'Precios y margen'],
          ['estructura', 'Estructura e inversión'], ['resultado', 'Resultado']].map(([k, l]) => (
          <button key={k} onClick={() => setPestana(k)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold ${pestana === k ? 'bg-emerald-600 text-white' : 'text-slate-500 hover:bg-slate-100'}`}>
            {l}
          </button>
        ))}
      </div>

      {/* ── Capacidad + coste por mueble ── */}
      {pestana === 'coste' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center gap-1">
              <Factory size={12} /> La fábrica
            </p>
            <div className="flex flex-wrap items-end gap-4">
              {[['personas', 'Personas', '1'], ['mueblesHora', 'Muebles/hora (equipo)', '0.1'],
                ['horasDia', 'Horas/día', '0.5'], ['diasSemana', 'Días/semana', '1'],
                ['horasAno', 'Horas productivas/año', '10'], ['costeHoraPersona', 'Coste €/hora por persona', '0.01']].map(([k, l, paso]) => (
                <div key={k}>
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">{l}</label>
                  <Casilla valor={datos?.capacidad?.[k]} paso={paso}
                    onChange={(v) => tocar(prev => ({ ...prev, capacidad: { ...prev.capacidad, [k]: v } }))} />
                </div>
              ))}
              <Dato label="Mano de obra / mueble" valor={eur(cap.manoObraPorMueble)} />
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Las horas son del EQUIPO, ya sin vacaciones ni festivos. La capacidad da por hecho que las dos personas están las mismas horas.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 overflow-x-auto">
            <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Coste del material (€ por mueble)</p>
              <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
                {[['mueble', 'Por mueble'], ['desglose', 'Desglosado']].map(([k, l]) => (
                  <button key={k} onClick={() => setModoCoste(k)}
                    className={`px-3 py-1 rounded-md text-[11px] font-bold ${modoCoste === k ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-500'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>

            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-[10px] uppercase text-slate-400">
                  <th className="text-left py-1 sticky left-0 bg-white">Referencia</th>
                  {modoCoste === 'mueble'
                    ? <th className="px-1 whitespace-nowrap">Material / mueble</th>
                    : MATERIALES.map(([k, l]) => <th key={k} className="px-1 whitespace-nowrap">{l}</th>)}
                  <th className="px-1">Material</th>
                  <th className="px-1">M. obra</th>
                  <th className="px-1">Coste directo</th>
                </tr>
              </thead>
              <tbody>
                {refs.map((r, i) => {
                  const calc = res?.referencias?.[i] || {};
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="py-1 font-black text-slate-700 sticky left-0 bg-white whitespace-nowrap">{r.nombre}</td>
                      {modoCoste === 'mueble' ? (
                        <td className="px-1">
                          <Casilla valor={r.costeMaterialesMueble} ancho="w-28"
                            titulo="Todo lo que se compra o se consume para ese mueble. SIN mano de obra: esa la calcula la fábrica."
                            onChange={(v) => cambiarRef(i, 'costeMaterialesMueble', v)} />
                        </td>
                      ) : MATERIALES.map(([k]) => (
                        <td key={k} className="px-1">
                          <Casilla valor={r[k]} ancho="w-20" onChange={(v) => cambiarRef(i, k, v)} />
                        </td>
                      ))}
                      <td className="px-1 text-right text-slate-500">
                        {eur(calc.materiales) || <span className="text-amber-600 text-xs">falta</span>}
                        {calc.fuente === 'por_mueble' && calc.materiales != null && (
                          <span className="block text-[9px] text-slate-400">a mano</span>
                        )}
                      </td>
                      <td className="px-1 text-right text-slate-500">{eur(calc.manoObra) || <span className="text-amber-600 text-xs">falta</span>}</td>
                      <td className="px-1 text-right font-black text-slate-800">{eur(calc.costeDirecto) || <span className="text-amber-600 text-xs">falta</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {modoCoste === 'mueble' ? (
              <p className="text-[11px] text-slate-400 mt-2">
                Todo lo que se compra o se consume para ese mueble: casco, herrajes, componentes y embalaje.
                <b className="text-slate-500"> Sin mano de obra</b> — esa sale sola de la fábrica ({eur(cap.manoObraPorMueble) || '…'} por mueble) y se suma aquí al lado.
                Si más adelante quieres saber dónde está el coste, pásate a «Desglosado».
              </p>
            ) : (
              <p className="text-[11px] text-slate-400 mt-2">
                Si falta una sola partida, el coste sale «falta»: un coste a medias no es un coste bajo, es un coste desconocido.
                {refs.some(r => r.costeMaterialesMueble != null) && (
                  <b className="text-amber-600"> Ojo: hay referencias con el coste puesto a mano, y ese manda sobre el desglose.</b>
                )}
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Precios y margen ── */}
      {pestana === 'precios' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-[10px] uppercase text-slate-400">
                  <th className="text-left py-1">Referencia</th>
                  <th className="px-2">Coste</th>
                  <th className="px-2">Precio B2B</th>
                  <th className="px-2">Margen B2B</th>
                  <th className="px-2">Precio B2C</th>
                  <th className="px-2">Margen B2C</th>
                </tr>
              </thead>
              <tbody>
                {refs.map((r, i) => {
                  const c = res?.referencias?.[i] || {};
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="py-1 font-black text-slate-700">{r.nombre}</td>
                      <td className="px-2 text-right text-slate-500">{eur(c.costeDirecto) || <span className="text-amber-600 text-xs">falta</span>}</td>
                      <td className="px-2"><Casilla valor={r.precioB2B} onChange={(v) => cambiarRef(i, 'precioB2B', v)} /></td>
                      <td className="px-2 text-right font-bold text-slate-700">
                        {c.margenB2B?.euros == null ? <span className="text-amber-600 text-xs">falta</span>
                          : <>{eur(c.margenB2B.euros)} <span className="text-slate-400 text-xs">({pct(c.margenB2B.porcentaje)})</span></>}
                      </td>
                      <td className="px-2"><Casilla valor={r.precioB2C} onChange={(v) => cambiarRef(i, 'precioB2C', v)} /></td>
                      <td className="px-2 text-right font-bold text-slate-700">
                        {c.margenB2C?.euros == null ? <span className="text-amber-600 text-xs">falta</span>
                          : <>{eur(c.margenB2C.euros)} <span className="text-slate-400 text-xs">({pct(c.margenB2C.porcentaje)})</span></>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-[11px] text-slate-400 mt-2">
              El margen va sobre el PRECIO DE VENTA: 100 de coste y 150 de venta son un 33 %, no un 50 %.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Lo que cuesta vender en B2C y no existe en B2B</p>
            <div className="flex flex-wrap items-end gap-4">
              {B2C.map(([k, l]) => (
                <div key={k}>
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">{l}</label>
                  <Casilla valor={datos?.b2c?.[k]}
                    onChange={(v) => tocar(prev => ({ ...prev, b2c: { ...prev.b2c, [k]: v } }))} />
                </div>
              ))}
              <Dato label="Margen contribución B2C" valor={eur(res?.margenB2CMedio)} />
            </div>
            <p className="text-[11px] text-slate-400 mt-2">Aquí un 0 sí vale: no pagar comisión es un dato.</p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">% de ventas en B2B (0,7 = 70 %)</label>
              <Casilla valor={datos?.repartoB2B} paso="0.05"
                onChange={(v) => tocar({ repartoB2B: v })} />
            </div>
            <Dato label="Margen medio ponderado" valor={eur(res?.margenMedioPonderado)} destacado />
            <Dato label="Precio medio ponderado" valor={eur(res?.precioMedio)} />
          </div>
        </div>
      )}

      {/* ── Estructura e inversión ── */}
      {pestana === 'estructura' && (
        <div className="grid md:grid-cols-2 gap-4">
          {[['estructura', 'Gastos de estructura (al año)'], ['inversion', 'Inversión inicial']].map(([clave, titulo]) => (
            <div key={clave} className="bg-white rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">{titulo}</p>
              <div className="space-y-1">
                {Object.entries(datos?.[clave] || {}).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-2">
                    <span className="text-[12px] text-slate-600">{k}</span>
                    <Casilla valor={v} paso="100"
                      onChange={(nv) => tocar(prev => ({ ...prev, [clave]: { ...prev[clave], [k]: nv } }))} />
                  </div>
                ))}
              </div>
              <div className="mt-3">
                <Dato label={`Total ${clave}`} valor={eur(res?.[clave]?.total, 0)} destacado />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Resultado ── */}
      {pestana === 'resultado' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            <Dato label="Facturación a plena capacidad" valor={eur(res?.facturacionPlenaCapacidad, 0)} />
            <Dato label="EBITDA a plena capacidad" valor={eur(res?.ebitdaPlenaCapacidad, 0)} destacado />
            <Dato label="Amortización anual" valor={eur(res?.amortizacionAnual, 0)} />
            <Dato label="Total inversión" valor={eur(res?.inversion?.total, 0)} />
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center gap-1">
              <TrendingUp size={12} /> Cuándo contratar a la tercera persona
            </p>
            <div className="flex flex-wrap items-end gap-4">
              <div>
                <label className="block text-[10px] font-black text-slate-400 uppercase mb-1">Plazo de entrega a prometer (semanas)</label>
                <Casilla valor={datos?.plazoEntregaSemanas} paso="1"
                  onChange={(v) => tocar({ plazoEntregaSemanas: v })} />
              </div>
              <Dato label="Capacidad semanal" valor={num(cap.capacidadSemanal)} nota="muebles/semana" />
              <Dato label="Cartera a partir de la cual contratar" valor={num(res?.carteraParaContratar)} destacado
                    nota="muebles pendientes, sostenido varias semanas" />
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              No por año de calendario: porque la cartera ya no cabe en la fábrica. Y antes de contratar, comprueba que el margen aguanta.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 overflow-x-auto">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Escenarios por personas</p>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[10px] uppercase text-slate-400">
                  <th className="text-left py-1">Escenario</th><th className="px-2">Personas</th>
                  <th className="px-2">Muebles/hora</th><th className="px-2">Capacidad</th>
                  <th className="px-2">Facturación</th><th className="px-2">EBITDA</th>
                </tr>
              </thead>
              <tbody>
                {(datos?.escenarios || []).map((e, i) => {
                  const c = res?.escenarios?.[i] || {};
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="py-1 font-black text-slate-700">{e.nombre}</td>
                      <td className="px-2 text-center text-slate-600">{e.personas}</td>
                      <td className="px-2 text-center">
                        <Casilla valor={e.mueblesHora} ancho="w-20" paso="0.1"
                          onChange={(v) => tocar(prev => ({
                            ...prev,
                            escenarios: prev.escenarios.map((x, j) => j === i ? { ...x, mueblesHora: v } : x),
                          }))} />
                      </td>
                      <td className="px-2 text-right text-slate-600">{num(c.capacidadAnual) || <span className="text-amber-600 text-xs">medir</span>}</td>
                      <td className="px-2 text-right text-slate-600">{eur(c.facturacion, 0) || <span className="text-amber-600 text-xs">—</span>}</td>
                      <td className="px-2 text-right font-bold text-slate-800">{eur(c.ebitda, 0) || <span className="text-amber-600 text-xs">—</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-[11px] text-amber-700 mt-2 flex items-start gap-1">
              <AlertTriangle size={12} className="mt-0.5 shrink-0" />
              La productividad de 3 y 4 personas se MIDE cuando pase. Suponer que tres rinden un 50 % más que dos es el número
              inventado que hunde un plan. Y el EBITDA descuenta la estructura de hoy: al contratar sube.
            </p>
          </div>
        </div>
      )}

      {listo && (
        <p className="mt-4 text-sm font-bold text-emerald-700 flex items-center gap-1">
          <CheckCircle2 size={15} /> El plan está completo: no falta ningún dato.
        </p>
      )}

      <button onClick={() => window.location.reload()} className="mt-6 self-start text-[11px] text-slate-400 hover:text-slate-600 flex items-center gap-1">
        <RefreshCw size={11} /> Recargar
      </button>
    </div>
  );
}
