// Catálogo de CASCOS / MÓDULOS EN KIT (Grupo ACB). Tarifa por tipo de módulo.
// Cada grupo: { tipo, grosor, fondo, colores:[...], dibujo, rows:[{alto, ancho, precios:{color:€}}], nota }
// precios: null = no disponible en ese color/medida.
// Se irá ampliando con 19mm, Diseño Grueso (Roble/Olmo) y Especiales Blanco.

// Helper para tablas Blanco/Aluminio (16 mm en kit). Filas: [alto, ancho, blanco, aluminio]
const BA = (rows) => rows.map(([alto, ancho, blanco, aluminio]) => ({
  alto, ancho, precios: { blanco: blanco, aluminio: aluminio },
}));

export const CASCOS_COLORES_16 = [
  { id: 'blanco', label: 'Blanco' },
  { id: 'aluminio', label: 'Aluminio' },
];

export const CASCOS_CATALOGO = [
  {
    id: 'bajo-balda-16', tipo: 'Bajo con balda', grosor: 16, fondo: 580, dibujo: 'bajo',
    colores: CASCOS_COLORES_16,
    nota: 'Los bajos de altura 700 y 800 llevan 1 balda.',
    rows: BA([
      [700, 150, null, 33.74], [700, 300, 34.47, 37.62], [700, 350, 36.25, 39.55], [700, 400, 38.06, 41.53],
      [700, 450, 40.19, 43.85], [700, 500, 42.77, 46.65], [700, 600, 45.65, 49.78], [700, 700, 50.29, 54.86],
      [700, 800, 54.75, 59.74], [700, 900, 58.56, 63.73], [700, 1000, 62.66, 68.20], [700, 1200, 70.95, 77.17],
      [800, 150, null, 36.03], [800, 300, 43.83, 52.35], [800, 350, 46.58, 55.00], [800, 400, 48.88, 58.09],
      [800, 450, 50.95, 61.18], [800, 500, 53.71, 64.27], [800, 600, 58.52, 70.47], [800, 700, 63.57, 76.42],
      [800, 800, 68.39, 82.60], [800, 900, 73.67, 88.79], [800, 1000, 79.64, 95.18], [800, 1200, 89.27, 107.13],
    ]),
  },
  {
    id: 'bajo-fregadero-16', tipo: 'Bajo fregadero', grosor: 16, fondo: 580, dibujo: 'bajo-fregadero',
    colores: CASCOS_COLORES_16,
    nota: 'Los bajos fregadero de altura 700 y 800 no llevan balda.',
    rows: BA([
      [700, 450, 34.04, null], [700, 500, 35.92, 39.20], [700, 600, 37.73, 41.17], [700, 700, 40.52, 44.21],
      [700, 800, 43.10, 47.02], [700, 900, 45.23, 49.35], [700, 1000, 47.54, null], [700, 1200, 52.94, 57.76],
      [700, 1350, null, 65.08],
      [800, 450, 40.46, null], [800, 500, 43.78, 48.60], [800, 600, 45.12, 51.01], [800, 700, 48.09, 53.44],
      [800, 800, 50.81, 56.10], [800, 900, 53.89, 58.75], [800, 1000, 57.14, null], [800, 1200, 62.85, 68.04],
      [800, 1350, null, 68.99],
    ]),
  },
  {
    id: 'bajo-terminal-16', tipo: 'Bajo terminal (puerta 35)', grosor: 16, fondo: 580, dibujo: 'bajo',
    colores: CASCOS_COLORES_16,
    rows: BA([[700, 300, null, 70.15], [800, 300, null, 74.34]]),
  },
  {
    id: 'bajo-angular-16', tipo: 'Bajo angular', grosor: 16, fondo: 580, dibujo: 'angular',
    colores: CASCOS_COLORES_16,
    nota: 'Los bajos rincón angular de altura 700 y 800 llevan 1 balda.',
    rows: BA([
      [700, 930, 126.42, 137.91], [700, 1030, null, 151.69], [700, 1080, 139.05, null],
      [800, 930, 155.14, 171.64], [800, 1030, null, 206.69], [800, 1080, 187.04, null],
    ]),
  },
  {
    id: 'alto-balda-16', tipo: 'Alto con balda', grosor: 16, fondo: 330, dibujo: 'alto',
    colores: CASCOS_COLORES_16,
    nota: 'Los altos 700 solo llevan 1 balda. Los altos 900 llevan 2 baldas.',
    rows: BA([
      [700, 300, 25.94, 28.00], [700, 350, 27.59, 29.88], [700, 400, 29.32, 31.73], [700, 450, 31.06, 33.61],
      [700, 500, 32.79, 35.39], [700, 600, 36.18, 39.12], [700, 700, 39.65, 42.85], [700, 800, 43.03, 46.68],
      [700, 900, 46.50, 50.41], [700, 1000, 49.88, 54.14],
      [900, 300, 29.93, 32.66], [900, 350, 31.82, 34.71], [900, 400, 34.04, 37.13], [900, 450, 36.76, 40.09],
      [900, 500, 38.71, 42.24], [900, 600, 43.67, 47.63], [900, 700, 46.70, 50.95], [900, 800, 51.56, 56.23],
      [900, 900, 55.49, 60.53], [900, 1000, 58.14, 63.44],
    ]),
  },
  {
    id: 'alto-platero-16', tipo: 'Alto platero con balda', grosor: 16, fondo: 330, dibujo: 'platero',
    colores: CASCOS_COLORES_16,
    nota: 'Los altos platero 700 no llevan balda. Los altos platero 900 solo llevan 1 balda.',
    rows: BA([
      [700, 600, 27.00, 29.39], [700, 700, 29.02, null], [700, 800, 31.04, 33.93], [700, 900, 33.04, 36.22],
      [900, 600, 35.91, 39.49], [900, 700, 41.09, null], [900, 800, 41.93, 47.83], [900, 900, 44.95, 49.65],
    ]),
  },
  {
    id: 'columna-despensero-16', tipo: 'Columna con baldas (despensero)', grosor: 16, fondo: 580, dibujo: 'columna',
    colores: CASCOS_COLORES_16,
    nota: 'Columna 2000: 3 baldas + 1 estante fijo. Columna 2200: 4 baldas + 1 estante fijo.',
    rows: BA([
      [2000, 400, 101.71, 110.96], [2000, 450, 107.48, 117.24], [2000, 600, 124.41, 135.73],
      [2200, 400, 118.90, 129.70], [2200, 450, 124.83, 136.18], [2200, 600, 145.54, 158.77],
    ]),
  },
  {
    id: 'columna-horno-16', tipo: 'Columna horno', grosor: 16, fondo: 580, dibujo: 'columna-horno',
    colores: CASCOS_COLORES_16,
    nota: 'Columna horno 2000/2200: 2 baldas + 3 estantes fijos.',
    rows: BA([[2000, 600, 107.34, null], [2200, 600, 119.56, null]]),
  },
  {
    id: 'columna-horno-micro-16', tipo: 'Columna horno-micro', grosor: 16, fondo: 580, dibujo: 'columna-horno',
    colores: CASCOS_COLORES_16,
    nota: 'Columna horno-micro 2000/2200: 2 baldas + 3 estantes fijos.',
    rows: BA([[2000, 600, 107.33, 117.81], [2200, 600, 119.56, 131.42]]),
  },
  {
    id: 'sobre-encimera-16', tipo: 'Sobre encimera', grosor: 16, fondo: 330, dibujo: 'columna',
    colores: CASCOS_COLORES_16,
    nota: 'Los muebles sobre encimera llevan 2 baldas.',
    rows: BA([[1300, 600, 63.01, null], [1450, 600, null, 58.66]]),
  },
];
