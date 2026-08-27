/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// Navegación entre módulos con VUELTA y sin perder el trabajo.
//
// El problema: cada módulo se monta y se desmonta al cambiar de pestaña, así que
// ir de Estudio 3D al analizador, de ahí al presupuesto y volver significaba
// empezar de cero tres veces. Aquí hay dos piezas:
//
//   1. `irA` deja una MIGA en `volverA` (una pila) antes de cambiar de pestaña,
//      y `volver` la consume. Sirve para cualquier recorrido, no solo el que
//      estaba escrito a mano para Estudio 3D.
//   2. `guardarSesion` / `leerSesion`: cada módulo deja una foto de su estado en
//      el estado global (que sí sobrevive al cambio de pestaña) y la recupera al
//      volver. Es memoria de la pestaña del navegador: si se recarga la página
//      se pierde, y por eso lo que deba conservarse de verdad se guarda en el
//      proyecto.

// Nombre legible de cada módulo, para el botón de volver.
export const NOMBRE_MODULO = {
  renderStudio: 'Estudio 3D',
  visualizer: 'Analizador de planos',
  budget: 'Presupuestador 2',
  presupuestador2: 'Presupuestador',
  cascos: 'Cocina Desmontada',
  armarios: 'Armarios',
  armarios2: 'Armarios 2',
  estudioCocinas: 'Estudio de cocinas',
  cocinasai: 'Cocinas IA',
  library: 'Proyectos',
  rentabilidad: 'Rentabilidad',
};

const MAX_MIGAS = 6;  // más de esto no es un recorrido, es estar perdido

export const irA = (setState, destino, extra = {}) => {
  if (!setState || !destino) return;
  setState(p => {
    const origen = p.currentTab;
    const pila = origen && origen !== destino
      ? [...(p.volverA || []).filter(t => t !== origen), origen].slice(-MAX_MIGAS)
      : (p.volverA || []);
    // `migaPara` ata la miga a ESTE destino: si luego te vas por el menú a otro
    // módulo, el "vienes de…" no te sigue por toda la aplicación.
    return { ...p, ...extra, volverA: pila, migaPara: destino, currentTab: destino };
  });
};

export const volver = (setState) => {
  if (!setState) return;
  setState(p => {
    const pila = [...(p.volverA || [])];
    const destino = pila.pop();
    return destino ? { ...p, currentTab: destino, volverA: pila, migaPara: destino } : p;
  });
};

export const limpiarVuelta = (setState) => setState(p => ({ ...p, volverA: [], migaPara: null }));

// ── Sesiones de módulo ───────────────────────────────────────────────────────
export const guardarSesion = (setState, clave, datos) => {
  if (!setState || !clave) return;
  setState(p => ({ ...p, sesiones: { ...(p.sesiones || {}), [clave]: datos } }));
};

export const leerSesion = (state, clave) => (state?.sesiones || {})[clave] || null;

export const borrarSesion = (setState, clave) => {
  if (!setState || !clave) return;
  setState(p => {
    const s = { ...(p.sesiones || {}) };
    delete s[clave];
    return { ...p, sesiones: s };
  });
};
