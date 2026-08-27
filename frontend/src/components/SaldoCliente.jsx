/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * SaldoCliente - Qué debe un cliente, con su detalle.
 *
 * Reúne en una sola pantalla lo que antes había que cuadrar a mano entre dos
 * sitios: sus facturas (Rentabilidad > Por líneas) y sus entregas a cuenta
 * (Ingresos a cuenta). Se busca por código o por nombre.
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Search, RefreshCw, Users, AlertTriangle, FileText, Banknote } from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });

const SaldoCliente = ({ onOpenDocument }) => {
  const [q, setQ] = useState('');
  const [clientes, setClientes] = useState([]);
  const [saldo, setSaldo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');

  // Lista de clientes con movimientos, para las sugerencias del buscador.
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_URL}/api/rentabilidad/clientes-saldo`, { headers: authHeaders() });
        const d = await r.json();
        if (r.ok) setClientes(d.items || []);
      } catch { /* el buscador funciona igual escribiendo el código a mano */ }
    })();
  }, []);

  const buscar = useCallback(async (texto) => {
    const busca = (texto ?? q).trim();
    if (!busca) return;
    setCargando(true); setError(''); setSaldo(null);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/saldo-cliente?q=${encodeURIComponent(busca)}`,
        { headers: authHeaders() });
      const d = await r.json();
      if (!r.ok) { setError(d.detail || `Error ${r.status}`); return; }
      setSaldo(d);
    } catch (e) {
      setError(`No se pudo consultar el saldo (${e?.message || 'error de red'}).`);
    } finally { setCargando(false); }
  }, [q]);

  const sugerencias = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t || saldo) return [];
    return clientes.filter(c =>
      (c.nombre || '').toLowerCase().includes(t) || String(c.codigo || '').toLowerCase().includes(t)
    ).slice(0, 8);
  }, [q, clientes, saldo]);

  return (
    <div className="space-y-4">
      {/* Buscador */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-1">
          <Users size={16} className="text-slate-400" />
          <h3 className="font-black text-sm uppercase text-slate-700">Saldo de cliente</h3>
          {clientes.length > 0 && (
            <span className="text-[11px] text-slate-400">{clientes.length} clientes con movimientos</span>
          )}
        </div>
        <p className="text-xs text-slate-500 mb-3">
          Escribe el código (por ejemplo <b>2759</b>) o el nombre. Se suman sus facturas y se
          restan sus entregas a cuenta.
        </p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={q}
              onChange={e => { setQ(e.target.value); setSaldo(null); setError(''); }}
              onKeyDown={e => e.key === 'Enter' && buscar()}
              placeholder="Código o nombre del cliente…"
              className="w-full pl-9 pr-3 py-2.5 border border-slate-200 rounded-xl text-sm"
            />
            {sugerencias.length > 0 && (
              <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
                {sugerencias.map((c, i) => (
                  <button key={i}
                    onClick={() => { setQ(c.codigo || c.nombre); buscar(c.codigo || c.nombre); }}
                    className="w-full text-left px-3 py-2 hover:bg-slate-50 text-sm flex items-center justify-between gap-2">
                    <span className="truncate">
                      {c.codigo && <span className="font-mono font-bold text-slate-500 mr-2">{c.codigo}</span>}
                      {c.nombre || '—'}
                    </span>
                    <span className="text-[11px] text-slate-400 shrink-0">
                      {c.facturas} fra · {c.ingresos} entr.
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => buscar()} disabled={cargando || !q.trim()}
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-900 disabled:opacity-50 text-white rounded-xl font-black text-sm flex items-center gap-2">
            {cargando ? <RefreshCw size={15} className="animate-spin" /> : <Search size={15} />}
            {cargando ? 'Buscando…' : 'Ver saldo'}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-2">{error}</p>}
      </div>

      {saldo && (
        <>
          {/* Cabecera con las cifras */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="flex items-baseline gap-2 mb-3">
              <h2 className="text-lg font-black text-slate-800">{saldo.cliente.nombre || '—'}</h2>
              {saldo.cliente.codigo && (
                <span className="font-mono text-sm font-bold text-slate-400">#{saldo.cliente.codigo}</span>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-indigo-600 text-white p-3 rounded-2xl">
                <p className="text-[10px] uppercase opacity-80">Facturado</p>
                <p className="text-2xl font-black">{eur(saldo.facturado)}</p>
              </div>
              <div className="bg-emerald-600 text-white p-3 rounded-2xl">
                <p className="text-[10px] uppercase opacity-80">Cobrado</p>
                <p className="text-2xl font-black">{eur(saldo.cobrado)}</p>
              </div>
              <div className={`${saldo.saldo > 0 ? 'bg-red-600' : 'bg-slate-800'} text-white p-3 rounded-2xl`}>
                <p className="text-[10px] uppercase opacity-80">
                  {saldo.saldo > 0 ? 'Pendiente de cobro' : saldo.saldo < 0 ? 'A favor del cliente' : 'Saldo'}
                </p>
                <p className="text-2xl font-black">{eur(Math.abs(saldo.saldo))}</p>
              </div>
            </div>
            {saldo.sinAplicarAFactura > 0 && (
              <div className="mt-3 flex items-start gap-2 text-xs bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-amber-800">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <span>
                  <b>{eur(saldo.sinAplicarAFactura)}</b> en entregas a cuenta que no están aplicadas a
                  ninguna factura. Descuentan del saldo, pero conviene asignarlas desde
                  «Ingresos a cuenta» para que cuadre factura a factura.
                </span>
              </div>
            )}
          </div>

          {/* Facturas */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
              <FileText size={14} className="text-slate-400" />
              <h3 className="font-black text-xs uppercase text-slate-600">Facturas ({saldo.facturas.length})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead className="bg-slate-100 text-slate-500">
                  <tr>
                    <th className="text-left p-2.5 font-black uppercase text-[10px]">Referencia</th>
                    <th className="text-left p-2.5 font-black uppercase text-[10px]">Fecha</th>
                    <th className="text-right p-2.5 font-black uppercase text-[10px]">Importe</th>
                    <th className="text-right p-2.5 font-black uppercase text-[10px]">Cobrado</th>
                    <th className="text-right p-2.5 font-black uppercase text-[10px]">Pendiente</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {saldo.facturas.map(f => (
                    <tr key={f.id} className="hover:bg-slate-50">
                      <td className="p-2.5">
                        {onOpenDocument ? (
                          <button onClick={() => onOpenDocument(f.ref)}
                            className="font-mono font-bold text-indigo-600 hover:underline">{f.ref || '—'}</button>
                        ) : <span className="font-mono font-bold">{f.ref || '—'}</span>}
                        {f.venta < 0 && <span className="ml-2 text-[10px] font-black text-rose-600 uppercase">abono</span>}
                      </td>
                      <td className="p-2.5 text-slate-500">{f.fecha || '—'}</td>
                      <td className="p-2.5 text-right font-mono">{eur(f.venta)}</td>
                      <td className="p-2.5 text-right font-mono text-emerald-700">{eur(f.cobrado)}</td>
                      <td className={`p-2.5 text-right font-mono font-bold ${f.pendiente > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                        {eur(f.pendiente)}
                      </td>
                    </tr>
                  ))}
                  {saldo.facturas.length === 0 && (
                    <tr><td colSpan={5} className="p-4 text-center text-slate-400 text-sm">Sin facturas.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Entregas a cuenta */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
              <Banknote size={14} className="text-slate-400" />
              <h3 className="font-black text-xs uppercase text-slate-600">Entregas a cuenta ({saldo.ingresos.length})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead className="bg-slate-100 text-slate-500">
                  <tr>
                    <th className="text-left p-2.5 font-black uppercase text-[10px]">Fecha</th>
                    <th className="text-left p-2.5 font-black uppercase text-[10px]">Concepto</th>
                    <th className="text-left p-2.5 font-black uppercase text-[10px]">Aplicada a</th>
                    <th className="text-right p-2.5 font-black uppercase text-[10px]">Importe</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {saldo.ingresos.map(i => (
                    <tr key={i.id} className={i.aplicadoAFactura ? 'hover:bg-slate-50' : 'bg-amber-50'}>
                      <td className="p-2.5 text-slate-500">{i.fecha || '—'}</td>
                      <td className="p-2.5">{i.concepto || '—'}</td>
                      <td className="p-2.5">
                        {i.targetRef
                          ? <span className="font-mono text-xs">{i.targetType || 'doc'} {i.targetRef}</span>
                          : <span className="text-[11px] font-bold text-amber-700 uppercase">sin aplicar</span>}
                      </td>
                      <td className="p-2.5 text-right font-mono font-bold text-emerald-700">{eur(i.importe)}</td>
                    </tr>
                  ))}
                  {saldo.ingresos.length === 0 && (
                    <tr><td colSpan={4} className="p-4 text-center text-slate-400 text-sm">Sin entregas a cuenta.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Documentos que NO entran en el saldo, para que no parezca que faltan. */}
          {saldo.otrosDocumentos.length > 0 && (
            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-3">
              <p className="text-[11px] text-slate-500">
                <b>Fuera del saldo:</b> {saldo.otrosDocumentos.map(d => `${d.docType} ${d.ref}`).join(' · ')}.
                Son presupuestos, pedidos o albaranes (o documentos ya convertidos en factura):
                contarlos duplicaría la misma venta.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SaldoCliente;
