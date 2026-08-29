/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { Layers, Box, Loader } from 'lucide-react';
import { MONTADA, DESMONTADA, NOMBRES, pestanasDe, hayQueEnseñarPestanas } from '../presupuestador';

const CocinaMontada3 = lazy(() => import('./CocinaMontada3'));
const Cascos = lazy(() => import('./Cascos'));

const ICONOS = { [MONTADA]: Layers, [DESMONTADA]: Box };

const Cargando = () => (
  <div className="h-full flex items-center justify-center text-dato-500">
    <Loader className="animate-spin mr-2" size={18} /> Cargando…
  </div>
);

/**
 * PRESUPUESTADOR: LAS DOS FORMAS DE PRESUPUESTAR UNA COCINA, EN UN SITIO.
 *
 * El master, 28/08: juntar Cocina Montada 3 y Cocina Desmontada bajo una sola
 * sección llamada «Presupuestador».
 *
 * SE JUNTA LA CARCASA, NO LOS MOTORES. Cada pestaña pinta la pantalla que ya
 * existía, sin tocarla por dentro, y cada una sigue guardando donde guardaba:
 * Montada 3 por tarifa MV y Desmontada en `cascos_orders`, con su expediente y
 * su compra al proveedor. Unificar el almacenamiento seria una migracion grande
 * y romperia justo lo que hace que COOP distinga el origen de cada pedido
 * (`services/origen_pedidos.py`).
 *
 * LAS DOS SE QUEDAN MONTADAS una vez visitadas, y eso no es un descuido: si se
 * desmontara la que no se ve, cambiar de pestaña vaciaría una relación a medio
 * hacer. Se ocultan con CSS, que conserva el estado y además el scroll.
 */
export default function PresupuestadorPanel({ currentUser, state, setState, logo, pestanaInicial }) {
  const pestanas = useMemo(() => pestanasDe(currentUser), [currentUser]);
  const [activa, setActiva] = useState(
    pestanas.includes(pestanaInicial) ? pestanaInicial : pestanas[0]);
  // Solo se monta lo que se ha llegado a abrir: la segunda pestaña no carga su
  // código hasta que se pulsa.
  const [vistas, setVistas] = useState(() => new Set([activa]));

  // Si cambian los permisos y la pestaña abierta deja de existir, se cae a la
  // primera que le quede. Sin esto se quedaría en blanco sin decir por qué.
  useEffect(() => {
    if (activa && !pestanas.includes(activa)) setActiva(pestanas[0]);
  }, [pestanas, activa]);

  // Entrar desde el menú viejo («Cocina Montada 3», «Cocina Desmontada») abre
  // su pestaña: los caminos de siempre tienen que seguir llevando al mismo
  // sitio, o el día del cambio se pierde medio mundo.
  useEffect(() => {
    if (pestanaInicial && pestanas.includes(pestanaInicial)) {
      setActiva(pestanaInicial);
      setVistas(v => new Set(v).add(pestanaInicial));
    }
  }, [pestanaInicial, pestanas]);

  const abrir = (id) => {
    setActiva(id);
    setVistas(v => new Set(v).add(id));
  };

  if (!pestanas.length) {
    return (
      <div className="h-full flex items-center justify-center p-6 text-center">
        <p className="text-sm font-bold text-dato-600">
          No tienes ningún presupuestador activo. Pídeselo al master.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {hayQueEnseñarPestanas(currentUser) && (
        /* `hueco-logo` deja sitio al logo flotante del ERP, que si no se come la
           primera pestaña. Y hacen scroll en horizontal para que en el móvil no
           se aplasten. */
        <div className="shrink-0 border-b border-slate-200 bg-white px-4 sm:px-8 pt-3 hueco-logo">
          <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto">
            {pestanas.map((id) => {
              const Icono = ICONOS[id];
              return (
                <button
                  key={id}
                  onClick={() => abrir(id)}
                  className={`px-3.5 py-2.5 sm:py-2 rounded-t-xl text-xs font-black uppercase tracking-widest flex items-center gap-1.5 whitespace-nowrap transition-colors ${
                    activa === id
                      ? 'bg-slate-50 text-accion-700 border border-b-0 border-slate-200'
                      : 'text-dato-500 hover:text-dato-700'}`}
                  data-testid={`presupuestador-tab-${id}`}
                >
                  <Icono size={14} /> {NOMBRES[id]}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0 relative">
        {/* CADA PESTAÑA CON SU PROPIO `Suspense`, no las dos dentro de uno.
            Compartiéndolo, abrir la segunda pestaña hace que el código de esa
            pestaña se esté cargando MIENTRAS la primera ya está pintada: el
            boundary tapa a las dos, esconde el DOM de la que ya estaba y lo
            vuelve a meter al terminar. Es mover por debajo lo que React cree
            tener colocado, y de ahí salen los `insertBefore` que tumban la
            aplicación entera. Con un boundary por pestaña, cargar una no toca
            la otra.

            Y se ocultan con CSS en vez de desmontarlas: así una relación a
            medio hacer no se pierde al mirar la otra pestaña. */}
        {vistas.has(MONTADA) && (
          <div className={`h-full ${activa === MONTADA ? '' : 'hidden'}`}>
            <Suspense fallback={<Cargando />}>
              <CocinaMontada3
                currentUser={currentUser}
                state={state}
                setState={setState}
                logo={logo}
              />
            </Suspense>
          </div>
        )}
        {vistas.has(DESMONTADA) && (
          <div className={`h-full ${activa === DESMONTADA ? '' : 'hidden'}`}>
            <Suspense fallback={<Cargando />}>
              <Cascos state={state} setState={setState} />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  );
}
