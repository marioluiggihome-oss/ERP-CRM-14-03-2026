/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * DESPIECE DE ARMARIOS 2 — lo que se corta de verdad.
 *
 * POR QUÉ ESTO VIVE FUERA DEL COMPONENTE
 * --------------------------------------
 * Porque es una CUENTA, y una cuenta hay que poder probarla. Mientras vivió
 * dentro del `useMemo` de `Armarios2.jsx` nadie la miró, y lo que hacía era
 * esto: toda balda salía de 400 mm y todo frente de cajón de 400 × 180,
 * dibujaras el cuerpo que dibujaras. En un armario de 2 m partido en dos, la
 * balda real mide unos 966 mm — o sea que el despiece pedía cortar menos de la
 * mitad de lo que hace falta.
 *
 * Y ese despiece no se queda en pantalla: se imprime en el PDF del cliente y se
 * exporta en CSV para cortar. Es exactamente la regla de la casa: NO SE INVENTA
 * NI UNA MEDIDA.
 *
 * TODO EN MILÍMETROS
 * ------------------
 * El configurador de armarios va en mm y la cocina en cm. Aquí entra mm y sale
 * mm, sin conversiones por el camino.
 *
 * DE DÓNDE SALEN LAS HOLGURAS
 * ---------------------------
 * Del despiece de `Armarios.jsx`, que es el que lleva años cortando, y de
 * `backend/services/armario_geometry.py`, que dibuja el alzado acotado. Las tres
 * cosas tienen que decir lo mismo o el plano estaría mintiendo sobre la pieza
 * que va a existir. `test_calculo_despiece_armarios2.py` compara las constantes
 * de los dos ficheros: si alguien cambia una sin cambiar la otra, el CI se pone
 * rojo.
 */

// ─── Holguras de fabricación (mm) ───────────────────────────────────────────
export const HOLGURA_BALDA = 6;         // la balda mide el hueco libre menos esto
export const HOLGURA_CAJON = 26;        // cuerpo del cajón = hueco libre − guías
export const HOLGURA_FRENTE = 8;        // frente de cajón, junta perimetral
export const ALTO_CAJON = 150;          // alto del cuerpo de un cajón
export const RETRANQUEO_INTERIOR = 20;  // baldas y divisores respecto al fondo
export const RETRANQUEO_CAJON = 50;     // fondo del cajón respecto al del armario

const num = (v) => (v === null || v === undefined || v === '' ? null : (Number.isFinite(Number(v)) ? Number(v) : null));

/**
 * Hueco libre del cuerpo `i`, en mm.
 *
 * `boundaries` son porcentajes del ancho: [0, ...divisores, 100]. Los divisores
 * se dibujan CENTRADOS sobre su posición, así que cada uno se come medio grueso
 * por cada lado; en los extremos el que se come el grueso entero es el costado.
 *
 * Se redondea HACIA ABAJO a propósito. Una balda un milímetro corta entra; una
 * balda un milímetro larga no entra, y eso es un viaje a fábrica.
 */
export function luzDeSeccion(i, { boundaries, width, thickness }) {
  const ancho = num(width), t = num(thickness);
  if (ancho === null || t === null || !Array.isArray(boundaries) || boundaries.length < 2) return null;
  const ultima = boundaries.length - 2;
  if (i < 0 || i > ultima) return null;
  const xIzq = (boundaries[i] / 100) * ancho;
  const xDer = (boundaries[i + 1] / 100) * ancho;
  const izq = i === 0 ? t : xIzq + t / 2;
  const der = i === ultima ? ancho - t : xDer - t / 2;
  return Math.max(0, Math.floor(der - izq));
}

// Orden en que se listan las piezas de un mismo cuerpo.
const ORDEN = ['shelf', 'drawer', 'hanging-rod', 'shoe-rack', 'pant-rack', 'led-strip'];

/**
 * Despiece completo. Devuelve filas
 * `{ p, q, medida, nota, tablero }` — `tablero: false` es herraje (barra,
 * zapatero, pantalonero, LED), que no se corta de un tablero y por eso no lleva
 * material.
 *
 * Si falta una medida del armario devuelve `[]`: un despiece a medias es peor
 * que ninguno, porque el de fábrica se lo cree.
 */
export function despiece({ cfg, comps, boundaries }) {
  const ancho = num(cfg && cfg.width), alto = num(cfg && cfg.height);
  const fondo = num(cfg && cfg.depth), t = num(cfg && cfg.thickness);
  if (ancho === null || alto === null || fondo === null || !t) return [];
  const piezas = (comps || []);
  const lim = Array.isArray(boundaries) && boundaries.length >= 2 ? boundaries : [0, 100];
  const nSec = lim.length - 1;

  const filas = [
    { p: 'Costado', q: 2, medida: `${alto} × ${fondo} × ${t}`, nota: '', tablero: true },
    { p: 'Techo', q: 1, medida: `${ancho - 2 * t} × ${fondo} × ${t}`, nota: '', tablero: true },
    { p: 'Base', q: 1, medida: `${ancho - 2 * t} × ${fondo} × ${t}`, nota: '', tablero: true },
  ];
  const nDiv = piezas.filter(c => c.type === 'divider-v').length;
  if (nDiv > 0) {
    filas.push({
      p: 'Divisor vertical', q: nDiv,
      medida: `${alto - 2 * t} × ${fondo - RETRANQUEO_INTERIOR} × ${t}`,
      nota: '', tablero: true,
    });
  }

  // Interior agrupado por cuerpo y tipo: 3 baldas en el cuerpo 2 son una línea
  // de 3 uds, no tres líneas sueltas que el de fábrica tiene que ir sumando.
  const grupos = new Map();
  piezas.filter(c => c.type !== 'divider-v').forEach(c => {
    const si = Math.min(Math.max(0, c.sectionIndex ?? 0), nSec - 1);
    const k = `${si}|${c.type}`;
    grupos.set(k, (grupos.get(k) || 0) + 1);
  });

  const claves = [...grupos.keys()].sort((a, b) => {
    const [sa, ta] = a.split('|'), [sb, tb] = b.split('|');
    return Number(sa) - Number(sb) || ORDEN.indexOf(ta) - ORDEN.indexOf(tb);
  });

  claves.forEach(k => {
    const [siTxt, tipo] = k.split('|');
    const si = Number(siTxt);
    const n = grupos.get(k);
    const luz = luzDeSeccion(si, { boundaries: lim, width: ancho, thickness: t });
    if (luz === null) return;
    const cuerpo = nSec > 1 ? `Cuerpo ${si + 1} · ` : '';
    const hueco = `${cuerpo}hueco libre ${luz}`;

    if (tipo === 'shelf') {
      filas.push({ p: 'Balda', q: n, medida: `${luz - HOLGURA_BALDA} × ${fondo - RETRANQUEO_INTERIOR} × ${t}`, nota: hueco, tablero: true });
    } else if (tipo === 'drawer') {
      filas.push({ p: 'Cajón (cuerpo)', q: n, medida: `${luz - HOLGURA_CAJON} × ${fondo - RETRANQUEO_CAJON} × ${ALTO_CAJON}`, nota: `${hueco} − guías`, tablero: true });
      filas.push({ p: 'Frente de cajón', q: n, medida: `${luz - HOLGURA_FRENTE} × ${ALTO_CAJON} × ${t}`, nota: hueco, tablero: true });
    } else if (tipo === 'hanging-rod') {
      filas.push({ p: 'Barra de colgar', q: n, medida: `${luz} de largo`, nota: `${cuerpo}corte de barra`, tablero: false });
    } else if (tipo === 'shoe-rack') {
      filas.push({ p: 'Zapatero', q: n, medida: `${luz} de hueco`, nota: `${cuerpo}herraje`, tablero: false });
    } else if (tipo === 'pant-rack') {
      filas.push({ p: 'Pantalonero', q: n, medida: `${luz} de hueco`, nota: `${cuerpo}herraje`, tablero: false });
    } else if (tipo === 'led-strip') {
      filas.push({ p: 'Tira LED', q: n, medida: `${luz} de largo`, nota: cuerpo.replace(/ · $/, ''), tablero: false });
    }
  });

  return filas;
}
