/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CocinaMontada3 — PRESUPUESTADOR MV A PANTALLA COMPLETA.
 *
 * QUÉ ES
 * ------
 * El mismo trabajo que se hacía dentro de una ventana en Cocina Desmontada
 * —elegir el grupo de precios, meter los muebles por código o por palabra,
 * decidir la mano de cada puerta y anotar observaciones— pero como PÁGINA
 * entera, con sus datos de presupuesto delante.
 *
 * POR QUÉ REUTILIZA EL MISMO COMPONENTE
 * -------------------------------------
 * Porque es el mismo trabajo. Tenerlo dos veces escrito es tenerlo dos veces
 * mal: se arregla la tarifa en un sitio, se olvida en el otro, y salen dos
 * presupuestos distintos de la misma cocina. `RelacionReview` sabe vivir de las
 * dos formas (`embebido`), y las reglas —tarifa, mano, coste tras el candado—
 * son exactamente las mismas en las dos.
 *
 * QUIÉN ENTRA
 * -----------
 * De momento SOLO EL MASTER. La comprobación está aquí Y en el menú, pero la
 * que vale de verdad es la del servidor: por aquí pasa el coste y el margen de
 * cada mueble, igual que en Rentabilidad.
 *
 * El permiso está preparado para abrirlo por jerarquía cuando toque
 * (`canUseMontada3`), sin tener que tocar el código: hoy no se lo damos a
 * nadie, y el día que se dé, se da en la ficha del usuario.
 */
import React, { useState } from 'react';
import { Lock, Layers, ArrowRight, CheckCircle2 } from 'lucide-react';
import { getToken } from '../services/api';
import RelacionReview from './RelacionReview';
import { irA } from '../services/navegacion';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const auth = () => ({ Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

/** Quién puede entrar. Master siempre; el permiso queda listo para la jerarquía. */
export const puedeUsarMontada3 = (u) => !!(
  u?.isAdmin || u?.isPrimaryAdmin || u?.isMaster || u?.canUseMontada3 === true
);

export default function CocinaMontada3({ state, setState }) {
  const u = state?.currentUser;
  const [cliente, setCliente] = useState('');
  const [referencia, setReferencia] = useState('');
  const [volcado, setVolcado] = useState(0);

  if (!puedeUsarMontada3(u)) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 p-8">
        <div className="max-w-md text-center">
          <Lock className="mx-auto text-slate-300" size={40} />
          <p className="mt-3 font-black text-slate-700">Cocina Montada 3 es solo del master.</p>
          <p className="text-sm text-slate-500 mt-1">
            Por aquí pasan el coste y el margen de cada mueble. Se abrirá por jerarquía cuando toque.
          </p>
        </div>
      </div>
    );
  }

  // Al confirmar, los muebles se mandan al presupuesto de Cocina Montada 2 por
  // el mismo canal que ya usan el analizador y el diseñador 3D. Se reutiliza
  // adrede: es plomería probada, y una tubería nueva para lo mismo es una
  // tubería más que puede gotear.
  const volcar = (muebles) => {
    const lineas = (muebles || []).map((m, i) => ({
      id: `mv3-${Date.now()}-${i}`,
      code: m.cod,
      name: `${m.tipo || 'Mueble'} ${m.ancho ? `${m.ancho} cm` : ''}${m.alto ? ` · alto ${m.alto}` : ''}`.trim(),
      quantity: m.qty || 1,
      // La observación viaja con la línea para poder imprimirla en el
      // presupuesto: escribirla y perderla al volcar es peor que no tenerla.
      nota: m.nota || '',
      width: m.ancho ? m.ancho * 10 : null,
      height: m.alto ? m.alto * 10 : null,
      depth: m.fondo ? m.fondo * 10 : null,
    }));
    setState(p => ({ ...p, p2PendingLines: lineas, p2PendingLibrary: 'MV' }));
    setVolcado(lineas.length);
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 min-w-0">
      <div className="hueco-logo shrink-0 px-4 py-2.5 bg-gradient-to-r from-slate-900 via-indigo-900 to-indigo-800 text-white flex items-center gap-3 flex-wrap">
        <h1 className="text-base font-black flex items-center gap-2">
          <Layers size={18} /> Cocina Montada 3
        </h1>
        <span className="text-[10px] font-black uppercase tracking-widest bg-white/20 px-2 py-0.5 rounded">Solo master</span>

        <div className="ml-auto flex items-center gap-2 flex-wrap">
          <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente"
            className="px-2.5 py-1 rounded-lg text-sm bg-white/95 text-slate-800 outline-none w-44" />
          <input value={referencia} onChange={e => setReferencia(e.target.value)} placeholder="Ref."
            className="px-2.5 py-1 rounded-lg text-sm bg-white/95 text-slate-800 outline-none w-28" />
        </div>
      </div>

      {volcado > 0 && (
        <div className="shrink-0 px-4 py-2 bg-emerald-50 border-b border-emerald-200 flex items-center gap-2 flex-wrap">
          <CheckCircle2 size={15} className="text-emerald-600" />
          <span className="text-sm font-bold text-emerald-800">
            {volcado} mueble(s) listos para el presupuesto{cliente ? ` de ${cliente}` : ''}.
          </span>
          <button onClick={() => irA(setState, 'presupuestador2')}
            className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-black bg-emerald-600 text-white hover:bg-emerald-700">
            Ir al presupuesto <ArrowRight size={13} />
          </button>
        </div>
      )}

      <div className="flex-1 min-h-0">
        <RelacionReview
          muebles={[]}
          noLeidas={[]}
          embebido
          textoConfirmar="Pasar al presupuesto"
          onConfirm={volcar}
          onClose={() => {}}
          apiUrl={API_URL}
          authHeaders={auth}
        />
      </div>
    </div>
  );
}
