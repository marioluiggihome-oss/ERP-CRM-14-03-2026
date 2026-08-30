/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { lazy, Suspense, useState } from 'react';
import { Users, Wallet, Loader, UserCog, Factory } from 'lucide-react';

const SociosCooperativistas = lazy(() => import('./SociosCooperativistas'));
const LiquidarMes = lazy(() => import('./LiquidarMes'));
const CoopUsuarios = lazy(() => import('./CoopUsuarios'));
const CoopProduccion = lazy(() => import('./CoopProduccion'));

/**
 * COOP: LA GESTIÓN DE LA COOPERATIVA, EN UN SOLO SITIO.
 *
 * El master, 28/08: «la gestión de la cooperativa la podemos hacer con el menú
 * de inicio, y con un botón que en vez de poner socios ponga COOP».
 *
 * Son dos pantallas y el orden no es casual: primero se asigna quién vendió y
 * quién montó cada pedido, y solo después se liquida. Al revés no se puede —
 * liquidar un pedido sin dueño no paga a nadie— y además congelaría el mes en
 * falso, porque lo liquidado no vuelve a entrar nunca.
 */
const PESTANAS = [
  { id: 'usuarios', label: 'Usuarios', icono: UserCog },
  { id: 'socios', label: 'Socios y pedidos', icono: Users },
  // PRODUCCIÓN va ANTES de liquidar, y el orden sigue sin ser casual: se
  // asigna quién montó, se mira por dónde va en fábrica, y solo cuando está
  // servido y cobrado se liquida. Es el mismo camino que recorre el dinero.
  { id: 'produccion', label: 'Producción', icono: Factory },
  { id: 'liquidar', label: 'Liquidar el mes', icono: Wallet },
];

export default function CoopPanel() {
  const [pestana, setPestana] = useState('usuarios');
  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* `hueco-logo` deja sitio al logo flotante del ERP, que si no se come la
          primera pestaña: se leía «OCIOS Y PEDIDOS». Y las pestañas hacen scroll
          en horizontal para que en el móvil no se aplasten unas contra otras. */}
      <div className="shrink-0 border-b border-slate-200 bg-white px-4 sm:px-8 pt-3 hueco-logo">
        <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto">
          {PESTANAS.map(({ id, label, icono: Icono }) => (
            <button
              key={id}
              onClick={() => setPestana(id)}
              className={`px-3 py-2 rounded-t-xl text-xs font-black uppercase tracking-widest flex items-center gap-1.5 transition-colors ${
                pestana === id
                  ? 'bg-slate-50 text-master-700 border border-b-0 border-slate-200'
                  : 'text-dato-500 hover:text-dato-700'}`}
              data-testid={`coop-tab-${id}`}
            >
              <Icono size={14} /> {label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <Suspense fallback={(
          <div className="h-full flex items-center justify-center text-dato-500">
            <Loader className="animate-spin mr-2" size={18} /> Cargando…
          </div>
        )}>
          {pestana === 'usuarios' && <CoopUsuarios />}
          {pestana === 'socios' && <SociosCooperativistas />}
          {pestana === 'produccion' && <CoopProduccion />}
          {pestana === 'liquidar' && <LiquidarMes />}
        </Suspense>
      </div>
    </div>
  );
}
