/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { lazy, Suspense, useState } from 'react';
import { Users, Wallet, Loader, UserCog, Factory, Receipt, Wrench, PiggyBank } from 'lucide-react';
import { esCooperativista } from '@/plataformas';

const SociosCooperativistas = lazy(() => import('./SociosCooperativistas'));
const LiquidarMes = lazy(() => import('./LiquidarMes'));
const CoopUsuarios = lazy(() => import('./CoopUsuarios'));
const CoopProduccion = lazy(() => import('./CoopProduccion'));
const AreaCooperativista = lazy(() => import('./AreaCooperativista'));
const Invoices = lazy(() => import('./Invoices'));
const AgendaMontajes = lazy(() => import('./AgendaMontajes'));

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
/**
 * LAS HERRAMIENTAS DE GESTIÓN CUELGAN DE AQUÍ, NO DE FUERA.
 *
 * El master, 30/08: «todas esas herramientas de gestión que cuelguen dentro del
 * área de COOP, no fuera», y «Mi área debería estar dentro de COOP».
 *
 * COOP deja de ser «el panel del master» y pasa a ser LA PLATAFORMA de la
 * cooperativa: dentro está todo lo suyo —quién es socio, qué pedidos hay, por
 * dónde van en fábrica, la facturación, la agenda de montajes y lo que cada uno
 * lleva ganado—.
 *
 * CADA PESTAÑA DICE QUIÉN LA VE, y esa es la parte que no se puede tocar a la
 * ligera. Al meter «Mi área» aquí dentro, COOP ya no puede seguir siendo solo
 * del master: si lo fuera, el cooperativista perdería su área — que es
 * exactamente el apagón del 28/08. Así que la puerta se abre también al socio,
 * y lo que se recorta son las PESTAÑAS, una por una.
 *
 * Los permisos de cada herramienta NO cambian por mudarse (regla 22): la
 * facturación sigue pidiendo lo que pedía, y la agenda también.
 */
// La misma lista del servidor (`services/master.py`): sin `isAdmin` desde el
// 29/08. Aquí decide QUÉ PESTAÑAS se ven; quien cierra de verdad es la API.
//
// VA ANTES DE `PESTANAS`, Y NO ES UN CAPRICHO DE ORDEN. La lista de abajo
// referencia esta función DIRECTAMENTE (`ve: esMaster`), no dentro de otra
// función, así que se lee al evaluar el módulo. Declarada después, un `const`
// está en su zona muerta temporal y el navegador lanza «Cannot access 'esMaster'
// before initialization» —minificado, «Cannot access 'z'»— y la pantalla entera
// no carga. Pasó el 30/08: tumbó COOP y con él «Mi área».
const esMaster = (u) => !!(u && (u.isMaster || u.isPrimaryAdmin));

const PESTANAS = [
  // Lo del socio va PRIMERO: es quien más veces entra, y entra a una sola cosa.
  { id: 'miarea', label: 'Mi área', icono: PiggyBank,
    ve: (u) => esCooperativista(u) },
  { id: 'usuarios', label: 'Usuarios', icono: UserCog, ve: esMaster },
  { id: 'socios', label: 'Socios y pedidos', icono: Users, ve: esMaster },
  // PRODUCCIÓN va ANTES de liquidar, y el orden sigue sin ser casual: se
  // asigna quién montó, se mira por dónde va en fábrica, y solo cuando está
  // servido y cobrado se liquida. Es el mismo camino que recorre el dinero.
  { id: 'produccion', label: 'Producción', icono: Factory, ve: esMaster },
  { id: 'montajes', label: 'Montajes', icono: Wrench,
    // La agenda conserva SU permiso: aquí solo cambia dónde se pinta.
    ve: (u) => esMaster(u) || u?.canAccessMontajes || u?.isMontador },
  { id: 'facturacion', label: 'Facturación', icono: Receipt,
    ve: (u) => esMaster(u) || u?.canAccessInvoices !== false },
  { id: 'liquidar', label: 'Liquidar el mes', icono: Wallet, ve: esMaster },
];

export default function CoopPanel({ currentUser, state, setState, pestanaInicial }) {
  const visibles = PESTANAS.filter(p => { try { return !!p.ve(currentUser); } catch { return false; } });
  // ABRE POR PRODUCCIÓN (master, 30/08: «al entrar en COOP que entre en
  // producción primero siempre»). Es lo que se mira a diario —por dónde va cada
  // cocina—; los socios se marcan una vez y la liquidación es de fin de mes.
  // ABRE POR LA PRIMERA QUE PUEDA VER. Para el master es Producción (30/08:
  // «al entrar en COOP que entre en producción primero siempre»); para un socio
  // que solo tiene «Mi área», abrir por Producción sería abrir en un 403.
  const [pestana, setPestana] = useState(() => {
    // Entrar por «Mi área» abre esa pestaña; si no, la de siempre.
    if (pestanaInicial && visibles.some(p => p.id === pestanaInicial)) return pestanaInicial;
    return (visibles.find(p => p.id === 'produccion') || visibles[0] || {}).id;
  });
  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* `hueco-logo` deja sitio al logo flotante del ERP, que si no se come la
          primera pestaña: se leía «OCIOS Y PEDIDOS». Y las pestañas hacen scroll
          en horizontal para que en el móvil no se aplasten unas contra otras. */}
      <div className="shrink-0 border-b border-slate-200 bg-white px-4 sm:px-8 pt-3 hueco-logo">
        <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto">
          {visibles.map(({ id, label, icono: Icono }) => (
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
          {pestana === 'miarea' && <AreaCooperativista />}
          {pestana === 'usuarios' && <CoopUsuarios />}
          {pestana === 'socios' && <SociosCooperativistas />}
          {pestana === 'produccion' && <CoopProduccion />}
          {pestana === 'montajes' && <AgendaMontajes currentUser={currentUser} />}
          {pestana === 'facturacion' && <Invoices currentUser={currentUser} />}
          {pestana === 'liquidar' && <LiquidarMes />}
          {!visibles.length && (
            <p className="p-8 text-center text-sm text-dato-500">
              Esta área es de la cooperativa y tu cuenta no tiene ninguna de sus
              secciones activada.
            </p>
          )}
        </Suspense>
      </div>
    </div>
  );
}
