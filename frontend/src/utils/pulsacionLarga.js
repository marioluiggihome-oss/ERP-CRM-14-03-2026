/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * MANTENER PULSADO: la forma de abrir un candado cuando no hay teclado.
 *
 * POR QUÉ EXISTE ESTO
 * -------------------
 * En el ERP el coste y el margen viven detrás de un candado que se abre con
 * Shift+clic. La idea es buena —no se abre por un roce, y no se abre delante de
 * un cliente sin querer— pero tiene un agujero que no se veía desde un
 * ordenador:
 *
 *     UNA TABLET NO TIENE TECLA SHIFT.
 *
 * O sea que en tablet y en móvil el margen no estaba «protegido»: estaba
 * INALCANZABLE. El botón se veía, se podía tocar, y no pasaba nada — que es la
 * peor forma de esconder algo, porque parece que está roto.
 *
 * LA SOLUCIÓN, Y POR QUÉ ESTA
 * ---------------------------
 * Mantener pulsado un segundo. Es un gesto DELIBERADO igual que Shift+clic: no
 * ocurre por rozar la pantalla ni por un clic de más, así que la protección
 * sigue siendo la misma. Y funciona en tablet, en móvil y con el ratón, con lo
 * cual el candado se abre igual en todas partes.
 *
 * Shift+clic se mantiene: quien ya lo tiene en los dedos no tiene que cambiar.
 *
 * CÓMO SE USA
 * -----------
 *     const largo = usePulsacionLarga(() => setVerCoste(v => !v));
 *     <button {...largo.props}
 *             onClick={(e) => {
 *               if (largo.consumir()) return;   // ya lo ha abierto la pulsación
 *               if (e.shiftKey) { abrir(); return; }
 *               ...lo que haga el clic normal...
 *             }}>
 *
 * `consumir()` existe porque al soltar el dedo el navegador manda TAMBIÉN un
 * clic. Sin esto, la pulsación larga abriría el candado y el clic de después lo
 * cerraría en el mismo gesto: el usuario ve un parpadeo y nada más.
 */
import { useCallback, useEffect, useRef } from 'react';

export const MS_PULSACION_LARGA = 600;

export function usePulsacionLarga(alMantener, { ms = MS_PULSACION_LARGA } = {}) {
  const temporizador = useRef(null);
  const yaDisparado = useRef(false);
  const accion = useRef(alMantener);
  accion.current = alMantener;

  const parar = useCallback(() => {
    if (temporizador.current) {
      clearTimeout(temporizador.current);
      temporizador.current = null;
    }
  }, []);

  // Si el componente se va mientras el dedo sigue apoyado, el temporizador se
  // quedaría vivo y dispararía sobre algo que ya no existe.
  useEffect(() => parar, [parar]);

  const empezar = useCallback(() => {
    yaDisparado.current = false;
    parar();
    temporizador.current = setTimeout(() => {
      temporizador.current = null;
      yaDisparado.current = true;
      accion.current();
    }, ms);
  }, [ms, parar]);

  return {
    props: {
      onPointerDown: empezar,
      onPointerUp: parar,
      // Si el dedo se sale del botón, es que se ha arrepentido: no cuenta.
      onPointerLeave: parar,
      onPointerCancel: parar,
      // Mantener pulsado en una pantalla táctil saca el menú de "copiar" y
      // selecciona el texto del botón. Aquí estorba las dos cosas.
      onContextMenu: (e) => e.preventDefault(),
      style: { WebkitTouchCallout: 'none', WebkitUserSelect: 'none', userSelect: 'none' },
    },
    /** ¿Este clic viene de una pulsación larga que ya ha hecho su trabajo? */
    consumir: () => {
      if (!yaDisparado.current) return false;
      yaDisparado.current = false;
      return true;
    },
  };
}

/** El texto de ayuda, escrito en un solo sitio para que no se contradiga. */
export const AYUDA_CANDADO = 'Mantén pulsado un segundo (o Shift+clic con ratón)';
