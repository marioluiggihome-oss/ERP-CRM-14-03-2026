/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useEffect, useState } from 'react';
import { TrendingUp, Clock, CheckCircle2, Wallet, AlertTriangle, Target } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', {
  minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

/**
 * EL ÁREA DEL COOPERATIVISTA.
 *
 * El master, 25/08/2026: «queremos un plan de estimulación continua, que cuando
 * accedan a su área puedan estar viendo lo que tienen que producir y los
 * beneficios que van a tener cuando lo produzcan».
 *
 * LOS TRES MONTONES NO SE SUMAN, y esa es la decisión de diseño de esta
 * pantalla. «En progreso», «a cobrar» y «cobrado» son promesas de distinto
 * valor: lo que está en progreso todavía se puede caer con el pedido. Un total
 * único que los mezclara sería enseñarle como suyo un dinero que aún no lo es —
 * y el día que un pedido se anule, la cifra baja sola y nadie entiende por qué.
 *
 * Los importes NO llevan color de estado (docs/DISENO.md): un importe no es ni
 * bueno ni malo. Destacan por tamaño y peso. El color se reserva para lo que sí
 * informa: lo que está a tiro, y las anomalías.
 */
const Monton = ({ icono: Icono, titulo, explica, euros, pedidos, tono }) => (
  <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex-1 min-w-0">
    <div className={`flex items-center gap-2 mb-1 ${tono}`}>
      <Icono size={15} />
      <span className="text-[11px] font-black uppercase tracking-wide">{titulo}</span>
    </div>
    <div className="text-3xl font-black text-dato-900 tabular-nums leading-tight">
      {eur(euros)}
    </div>
    <div className="text-[11px] text-dato-500 mt-1">
      {pedidos === 1 ? '1 pedido' : `${pedidos} pedidos`} · {explica}
    </div>
  </div>
);

export default function AreaCooperativista() {
  const [area, setArea] = useState(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const t = localStorage.getItem('token');
        const r = await fetch(`${API_URL}/api/cooperativistas/mi-area`, {
          headers: t ? { Authorization: `Bearer ${t}` } : {},
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) { setError(d.detail || 'No se pudo cargar tu área.'); return; }
        setArea(d.area);
      } catch (e) {
        // Se DICE que no se pudo leer. Un área en blanco sin explicación se
        // interpreta como «no he ganado nada», que es muy distinto.
        setError('No se pudo conectar. Vuelve a intentarlo en un momento.');
      } finally { setCargando(false); }
    })();
  }, []);

  if (cargando) {
    return (
      <div className="p-6 space-y-3" aria-live="polite">
        <p className="text-sm font-bold text-dato-600">Cargando tu área…</p>
        {[0, 1].map(i => (
          <div key={i} className="h-24 rounded-2xl bg-slate-100 animate-pulse"
            style={{ animationDelay: `${i * 140}ms` }} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-2xl border border-error-200 bg-error-50/60 p-5">
          <p className="font-bold text-error-800 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const esMontador = area?.rol === 'montador';
  const aTiro = area?.aTiro || [];
  const anomalias = ['enProgreso', 'consolidada']
    .flatMap(k => (area?.[k]?.lineas || []).filter(l => l.anomalia));

  return (
    <div className="p-4 sm:p-6 space-y-5 max-w-5xl mx-auto">
      {/* `hueco-logo` deja sitio al logo flotante del ERP. Sin esto el logo se
          come el principio del título: en el móvil ponía «rea» en vez de «Mi
          área», que parece un fallo de la pantalla y es solo un solape. */}
      <div className="hueco-logo">
        <h1 className="text-xl font-black text-dato-900">Mi área</h1>
        <p className="text-[13px] text-dato-500">
          {esMontador ? 'Comisión de montaje' : 'Comisión comercial'} · se liquida una vez al mes
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Monton icono={Clock} titulo="En progreso" tono="text-aviso-700"
          explica="aceptados, aún no cobrados"
          euros={area?.enProgreso?.euros} pedidos={area?.enProgreso?.pedidos} />
        <Monton icono={CheckCircle2} titulo="A cobrar" tono="text-ok-700"
          explica="servidos y cobrados"
          euros={area?.consolidada?.euros} pedidos={area?.consolidada?.pedidos} />
        <Monton icono={Wallet} titulo="Ya cobrado" tono="text-dato-500"
          explica="liquidado en su mes"
          euros={area?.liquidada?.euros} pedidos={area?.liquidada?.pedidos} />
      </div>

      {/* NO hay un total que sume los tres. Ver la nota de arriba. */}
      <p className="text-[11px] text-dato-400 -mt-2">
        Los tres no se suman: lo que está en progreso todavía depende de que el
        pedido se sirva y se cobre.
      </p>

      {!esMontador && aTiro.length > 0 && (
        <div className="rounded-2xl border border-accion-200 bg-accion-50/50 p-5">
          <div className="flex items-center gap-2 mb-3 text-accion-800">
            <Target size={16} />
            <span className="text-[11px] font-black uppercase tracking-wide">
              Lo que tienes a tiro
            </span>
          </div>
          <div className="space-y-2.5">
            {aTiro.map(t => (
              <div key={t.pedidoId}
                className="rounded-xl bg-white border border-accion-100 p-3.5">
                <p className="text-[13px] text-dato-700 leading-relaxed">
                  Al pedido <span className="font-mono font-bold">{t.pedidoId}</span> le
                  faltan <span className="font-black text-dato-900">{eur(t.faltan)}</span> para
                  pasar de {eur(t.porMuebleAhora)} a{' '}
                  <span className="font-black text-dato-900">{eur(t.porMuebleSiSalta)}</span> por
                  mueble.
                </p>
                <p className="text-[13px] mt-1.5 text-accion-800 font-bold">
                  Con sus {t.muebles} muebles son {eur(t.extraTotal)} más para ti.
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {anomalias.length > 0 && (
        <div className="rounded-2xl border border-aviso-300 bg-aviso-50/60 p-4">
          <div className="flex items-center gap-2 mb-1.5 text-aviso-800">
            <AlertTriangle size={15} />
            <span className="text-[11px] font-black uppercase tracking-wide">
              {anomalias.length === 1 ? 'Un pedido' : `${anomalias.length} pedidos`} con algo raro
            </span>
          </div>
          <p className="text-[12px] text-dato-600">
            Salieron del almacén sin estar cobrados del todo, así que su comisión
            no se libera. Coméntalo con administración:{' '}
            <span className="font-mono font-bold">
              {anomalias.map(a => a.pedidoId).join(', ')}
            </span>
          </p>
        </div>
      )}

      {!area?.enProgreso?.pedidos && !area?.consolidada?.pedidos
        && !area?.liquidada?.pedidos && (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <TrendingUp size={36} className="mx-auto text-dato-300 mb-3" />
          <p className="font-bold text-dato-700">Todavía no tienes pedidos asignados</p>
          <p className="text-[12px] text-dato-500 mt-1">
            En cuanto se te asigne uno aparecerá aquí, con lo que llevas ganado.
          </p>
        </div>
      )}
    </div>
  );
}
