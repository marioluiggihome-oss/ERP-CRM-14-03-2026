/**
 * RevisionFichas — Pantalla de REVISIÓN de la rentabilidad.
 *
 * Dos comprobaciones, ambas de SOLO LECTURA (no modifican nada):
 *  1) Auditoría de revisiones: qué fichas ya revisadas se han quedado obsoletas
 *     (cambiaron después del visto bueno), cuáles se revisaron antes de existir
 *     la huella y cuáles tienen el margen sospechoso del fallo de coste.
 *  2) Contraste con el LISTADO OFICIAL de facturas: qué facturas faltan por
 *     importar y cuáles descuadran (síntoma de páginas perdidas al importar).
 */
import React, { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, AlertTriangle, FileWarning, Upload, RefreshCw, Search, FileText } from 'lucide-react';
import { authHeaders } from '../services/api';

const API = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

export default function RevisionFichas({ onOpenDocument }) {
  const [aud, setAud] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [listado, setListado] = useState(null);
  const [subiendo, setSubiendo] = useState(false);

  const cargarAuditoria = useCallback(async () => {
    setCargando(true); setError(null);
    try {
      const r = await fetch(`${API}/api/rentabilidad/auditoria-revisiones`, { headers: authHeaders() });
      const d = await r.json();
      if (!r.ok || !d.success) throw new Error(d.detail || 'No se pudo cargar la auditoría');
      setAud(d);
    } catch (e) { setError(e.message); } finally { setCargando(false); }
  }, []);

  useEffect(() => { cargarAuditoria(); }, [cargarAuditoria]);

  const subirListado = async (file) => {
    if (!file) return;
    setSubiendo(true); setError(null);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API}/api/rentabilidad/verificar-listado`, {
        method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const d = await r.json();
      if (!r.ok || !d.success) throw new Error(d.detail || 'No se pudo leer el listado');
      setListado(d);
    } catch (e) { setError(e.message); } finally { setSubiendo(false); }
  };

  const Tarjeta = ({ icono: Ic, color, titulo, valor, nota }) => (
    <div className="bg-white rounded-2xl border border-slate-200 p-4">
      <div className={`flex items-center gap-2 ${color}`}><Ic size={16} />
        <span className="text-[10px] font-black uppercase tracking-wider">{titulo}</span>
      </div>
      <p className="text-2xl font-black text-slate-800 mt-1">{valor}</p>
      {nota && <p className="text-[11px] text-slate-400">{nota}</p>}
    </div>
  );

  const Fila = ({ f, extra }) => (
    <tr className="border-b border-slate-100 hover:bg-slate-50">
      <td className="py-1.5">
        <button onClick={() => onOpenDocument?.(f.ref)}
          className="font-black text-indigo-700 hover:underline">{f.ref || '—'}</button>
      </td>
      <td className="text-slate-600 text-xs">{(f.cliente || '').slice(0, 30)}</td>
      <td className="text-slate-400 text-xs">{(f.fecha || '').slice(0, 10)}</td>
      <td className="text-right text-slate-600">{eur(f.venta)}</td>
      <td className="text-right text-slate-600">{eur(f.coste)}</td>
      {extra}
    </tr>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-lg font-black text-slate-800 flex items-center gap-2">
            <ShieldCheck size={20} className="text-emerald-600" /> Revisión de fichas
          </h3>
          <p className="text-xs text-slate-500">Comprobación de solo lectura: no modifica ningún dato.</p>
        </div>
        <button onClick={cargarAuditoria} disabled={cargando}
          className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold text-xs disabled:opacity-50">
          <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} /> Actualizar
        </button>
      </div>

      {error && <div className="text-sm px-3 py-2 rounded-lg bg-red-50 text-red-700 border border-red-200">{error}</div>}

      {/* ── 1. Auditoría de revisiones ── */}
      {aud && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Tarjeta icono={ShieldCheck} color="text-emerald-600" titulo="Coherentes"
              valor={aud.resumen.coherentes} nota="cuadran con su huella" />
            <Tarjeta icono={AlertTriangle} color="text-amber-600" titulo="Caducadas"
              valor={aud.resumen.caducadas} nota="cambiaron tras revisarse" />
            <Tarjeta icono={FileWarning} color="text-slate-500" titulo="Sin huella"
              valor={aud.resumen.sinHuella} nota="revisadas antes; reverificar" />
            <Tarjeta icono={AlertTriangle} color="text-red-600" titulo="Coste sospechoso"
              valor={aud.resumen.sospechosasCoste} nota="margen negativo con costes" />
          </div>

          {aud.sospechosas?.length > 0 && (
            <div className="bg-white rounded-2xl border border-red-200 p-4">
              <h4 className="font-black text-red-700 text-sm mb-2">Margen negativo teniendo costes cargados</h4>
              <p className="text-[11px] text-slate-500 mb-2">Patrón del fallo de coste (se cargó la tarifa bruta en vez del neto con descuento). Revisa estas primero.</p>
              <table className="w-full text-sm">
                <thead><tr className="text-[10px] uppercase text-slate-400 border-b">
                  <th className="text-left py-1">Factura</th><th className="text-left">Cliente</th><th className="text-left">Fecha</th>
                  <th className="text-right">Venta</th><th className="text-right">Coste</th><th className="text-right">Margen</th></tr></thead>
                <tbody>{aud.sospechosas.map(f => (
                  <Fila key={f.id} f={f} extra={<td className="text-right font-bold text-red-600">{eur(f.margen)}</td>} />
                ))}</tbody>
              </table>
            </div>
          )}

          {aud.caducadas?.length > 0 && (
            <div className="bg-white rounded-2xl border border-amber-200 p-4">
              <h4 className="font-black text-amber-700 text-sm mb-2">Revisiones caducadas</h4>
              <p className="text-[11px] text-slate-500 mb-2">La ficha cambió DESPUÉS de darle el visto bueno: el sello ya no corresponde a estos datos.</p>
              <table className="w-full text-sm">
                <thead><tr className="text-[10px] uppercase text-slate-400 border-b">
                  <th className="text-left py-1">Factura</th><th className="text-left">Cliente</th><th className="text-left">Fecha</th>
                  <th className="text-right">Venta</th><th className="text-right">Coste</th><th className="text-right">Dif. venta</th></tr></thead>
                <tbody>{aud.caducadas.map(f => (
                  <Fila key={f.id} f={f} extra={<td className={`text-right font-bold ${f.difVenta < 0 ? 'text-red-600' : 'text-emerald-600'}`}>{eur(f.difVenta)}</td>} />
                ))}</tbody>
              </table>
            </div>
          )}

          {aud.sinHuella?.length > 0 && (
            <details className="bg-white rounded-2xl border border-slate-200 p-4">
              <summary className="font-black text-slate-700 text-sm cursor-pointer">
                Revisadas sin huella ({aud.sinHuella.length}) — conviene reverificar
              </summary>
              <p className="text-[11px] text-slate-500 my-2">Se revisaron antes de que el sistema guardara sobre qué se firmaba. No se puede saber si los datos han cambiado desde entonces.</p>
              <table className="w-full text-sm">
                <thead><tr className="text-[10px] uppercase text-slate-400 border-b">
                  <th className="text-left py-1">Factura</th><th className="text-left">Cliente</th><th className="text-left">Fecha</th>
                  <th className="text-right">Venta</th><th className="text-right">Coste</th><th className="text-right">Revisó</th></tr></thead>
                <tbody>{aud.sinHuella.map(f => (
                  <Fila key={f.id} f={f} extra={<td className="text-right text-[11px] text-slate-400">{f.revisadaPor}</td>} />
                ))}</tbody>
              </table>
            </details>
          )}
        </>
      )}

      {/* ── 2. Contraste con el listado oficial ── */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <h4 className="font-black text-slate-700 text-sm flex items-center gap-2 mb-1">
          <FileText size={15} className="text-indigo-600" /> Contrastar con el listado oficial de facturas
        </h4>
        <p className="text-[11px] text-slate-500 mb-3">
          Sube el informe de facturas (el PDF con nº, fecha, cliente y base). Compara la base oficial con lo importado
          y detecta las que faltan y las que descuadran (síntoma de páginas perdidas).
        </p>
        <label className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs cursor-pointer">
          {subiendo ? <RefreshCw size={14} className="animate-spin" /> : <Upload size={14} />}
          {subiendo ? 'Analizando…' : 'Subir listado (PDF)'}
          <input type="file" accept="application/pdf" className="hidden"
            onChange={(e) => subirListado(e.target.files?.[0])} />
        </label>

        {listado && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Tarjeta icono={FileText} color="text-slate-500" titulo="En el listado" valor={listado.enListado} />
              <Tarjeta icono={ShieldCheck} color="text-emerald-600" titulo="Correctas" valor={listado.correctas} />
              <Tarjeta icono={FileWarning} color="text-amber-600" titulo="No importadas" valor={listado.resumen.noImportadas} />
              <Tarjeta icono={AlertTriangle} color="text-red-600" titulo="Descuadran"
                valor={listado.resumen.conDescuadre} nota={`${eur(listado.resumen.importeNoRegistrado)} sin registrar`} />
            </div>

            {listado.descuadres?.length > 0 && (
              <div>
                <h5 className="text-xs font-black text-red-700 mb-1">Facturas que descuadran</h5>
                <table className="w-full text-sm">
                  <thead><tr className="text-[10px] uppercase text-slate-400 border-b">
                    <th className="text-left py-1">Factura</th><th className="text-left">Cliente</th>
                    <th className="text-right">Base oficial</th><th className="text-right">Importado</th>
                    <th className="text-right">Diferencia</th><th className="text-right">Líneas</th></tr></thead>
                  <tbody>{listado.descuadres.map(d => (
                    <tr key={d.ref} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-1.5">
                        <button onClick={() => onOpenDocument?.(d.ref)} className="font-black text-indigo-700 hover:underline">{d.ref}</button>
                      </td>
                      <td className="text-slate-600 text-xs">{(d.cliente || '').slice(0, 28)}</td>
                      <td className="text-right text-slate-600">{eur(d.base)}</td>
                      <td className="text-right text-slate-600">{eur(d.ventaImportada)}</td>
                      <td className={`text-right font-bold ${d.diferencia < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                        {eur(d.diferencia)}{d.sospechaPaginasPerdidas ? ' ⚠️' : ''}
                      </td>
                      <td className="text-right text-slate-500">{d.lineas}</td>
                    </tr>
                  ))}</tbody>
                </table>
                <p className="text-[11px] text-slate-400 mt-1">⚠️ = falta importe respecto a la factura real: probablemente se perdieron líneas al importar.</p>
              </div>
            )}

            {listado.faltanPorImportar?.length > 0 && (
              <details>
                <summary className="text-xs font-black text-amber-700 cursor-pointer">
                  No importadas ({listado.faltanPorImportar.length})
                </summary>
                <div className="text-xs text-slate-600 mt-2 grid grid-cols-2 sm:grid-cols-4 gap-1">
                  {listado.faltanPorImportar.map(f => (
                    <span key={f.ref} className="bg-amber-50 px-2 py-1 rounded">{f.ref} · {eur(f.base)}</span>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>

      {!aud && !cargando && (
        <div className="text-center text-slate-400 py-8 text-sm flex flex-col items-center gap-2">
          <Search size={28} className="opacity-40" /> Pulsa «Actualizar» para lanzar la revisión.
        </div>
      )}
    </div>
  );
}
