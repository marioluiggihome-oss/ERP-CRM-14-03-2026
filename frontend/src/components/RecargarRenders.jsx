/**
 * RecargarRenders — saldo de renders del usuario y compra de packs.
 *
 * Antes, quien agotaba su cupo tenía que esperar a que el administrador le
 * cargara un pack a mano. Aquí lo compra él mismo con tarjeta y el saldo se
 * abona solo cuando el cobro se confirma.
 *
 * Los renders comprados NO caducan a fin de mes; los del plan sí, y por eso se
 * gastan primero.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Zap, X, CreditCard, Loader, AlertTriangle, Check } from 'lucide-react';
import { authHeaders } from '../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

export default function RecargarRenders({ abierto, onClose }) {
  const [saldo, setSaldo] = useState(null);
  const [cat, setCat] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [comprando, setComprando] = useState('');
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true); setError('');
    try {
      const [rc, rp] = await Promise.all([
        fetch(`${BASE}/api/ai-engine/my-credits`, { headers: authHeaders() }),
        fetch(`${BASE}/api/render-packs/catalogo`, { headers: authHeaders() }),
      ]);
      if (rc.ok) setSaldo(await rc.json());
      if (rp.ok) setCat(await rp.json());
      else setError('No se pudo cargar el catálogo de packs.');
    } catch (e) {
      setError(`No se pudo consultar tu saldo (${e?.message || 'error de red'}).`);
    } finally { setCargando(false); }
  }, []);

  useEffect(() => { if (abierto) cargar(); }, [abierto, cargar]);

  const comprar = async (packId) => {
    setComprando(packId); setError('');
    try {
      const r = await fetch(`${BASE}/api/render-packs/comprar`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ packId }),
      });
      const d = await r.json();
      if (!r.ok) { setError(d.detail || `Error ${r.status}`); return; }
      // La pasarela de Stripe se abre en esta misma pestaña; al terminar
      // devuelve al ERP con ?recarga=ok
      window.location.href = d.url;
    } catch (e) {
      setError(`No se pudo abrir la pasarela de pago (${e?.message || 'error de red'}).`);
    } finally { setComprando(''); }
  };

  if (!abierto) return null;

  const ilimitado = saldo?.ilimitado;
  const restantes = Number(saldo?.restantes || 0);
  const comprados = Number(saldo?.saldo || 0);

  return (
    <div className="fixed inset-0 bg-black/50 z-[170] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[88vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="bg-gradient-to-r from-amber-500 to-orange-600 text-white px-5 py-3 flex items-center justify-between shrink-0">
          <h3 className="font-black text-sm uppercase flex items-center gap-2"><Zap size={16} /> Tus renders de IA</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4">
          {cargando && <p className="text-sm text-slate-500 flex items-center gap-2"><Loader size={14} className="animate-spin" /> Cargando…</p>}

          {ilimitado ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-800 font-bold flex items-center gap-2">
              <Check size={16} /> Tu cuenta tiene renders ilimitados.
            </div>
          ) : saldo && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className={`${restantes > 0 ? 'bg-slate-800' : 'bg-red-600'} text-white p-3 rounded-2xl`}>
                <p className="text-[10px] uppercase opacity-80">Te quedan</p>
                <p className="text-2xl font-black">{restantes}</p>
              </div>
              <div className="bg-white border border-slate-200 p-3 rounded-2xl">
                <p className="text-[10px] uppercase text-slate-400">Del plan este mes</p>
                <p className="text-2xl font-black text-slate-700">{saldo.asignados || 0}</p>
                <p className="text-[10px] text-slate-400">se renuevan cada mes</p>
              </div>
              <div className="bg-white border border-slate-200 p-3 rounded-2xl">
                <p className="text-[10px] uppercase text-slate-400">Comprados</p>
                <p className="text-2xl font-black text-amber-600">{comprados}</p>
                <p className="text-[10px] text-emerald-600 font-bold">no caducan</p>
              </div>
            </div>
          )}

          {!ilimitado && restantes === 0 && (
            <div className="flex items-start gap-2 text-sm bg-red-50 border border-red-200 rounded-lg p-3 text-red-800">
              <AlertTriangle size={15} className="shrink-0 mt-0.5" />
              <span>Te has quedado sin renders. Recarga para seguir generando.</span>
            </div>
          )}

          {error && <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-2">{error}</p>}

          {cat && !ilimitado && (
            <>
              <h4 className="font-black text-xs uppercase text-slate-500 pt-1">Recargar</h4>
              {!cat.pagoTarjeta && (
                <p className="text-xs bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-amber-800">
                  El pago con tarjeta aún no está activado. Pide la recarga al administrador
                  indicándole el pack que quieres.
                </p>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {(cat.packs || []).map(p => (
                  <div key={p.id} className="border border-slate-200 rounded-2xl p-4 flex flex-col">
                    <p className="font-black text-slate-800">{p.renders} renders</p>
                    <p className="text-[11px] text-slate-400 mb-2">{eur(p.porRender)} por render</p>
                    <p className="text-2xl font-black text-slate-800">{eur(p.precioConIva)}</p>
                    <p className="text-[11px] text-slate-400 mb-3">{eur(p.precioSinIva)} + {cat.iva}% IVA</p>
                    <button
                      onClick={() => comprar(p.id)}
                      disabled={!cat.pagoTarjeta || !!comprando}
                      className="mt-auto w-full py-2 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                      {comprando === p.id ? <Loader size={14} className="animate-spin" /> : <CreditCard size={14} />}
                      {comprando === p.id ? 'Abriendo…' : 'Comprar'}
                    </button>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-slate-400">
                Los renders comprados se suman a tu saldo y <b>no caducan</b>. Primero se gastan
                los del plan del mes; el saldo comprado solo se toca cuando aquellos se agotan.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
