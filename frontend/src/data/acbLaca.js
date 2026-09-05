/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// TARIFA DE LACADOS DEL GRUPO ACB (ACB Lacados S.L.), 2026 — págs. 5 a 16.
//
// Se genera con `herramientas/tarifa_acb_laca.py`, que VALIDA los números
// antes de escribir nada. Es la segunda colección de ACB: la primera, el
// CANTEADO, vive en `acbPuertas.js`.
//
// LA LACA NO SE TARIFA COMO EL CANTEADO. Allí el precio sale de una matriz por
// serie; aquí sale de tres pasos encadenados:
//
//     precio = matriz(GRUPO, acabado, alto, ancho) × (1 + recargo del modelo)
//
// El modelo dice a qué GRUPO pertenece y qué recargo lleva, y eso DEPENDE DEL
// GRUESO: un ALZIRA de 19 mm es GRUPO 3 a secas y el de 22 mm es GRUPO 3 + 5 %.
// Encima van, si los hay, el color especial, el XOLID y la decoración.
//
// PRECIOS DE TARIFA, ANTES DE DESCUENTO. El de ACB lo teclea el master, porque
// se negocia y cambia (igual que en los cascos y en el canteado).

/** Las cuatro columnas de precio de cada matriz de grupo. */
export const ACB_LACA_ACABADOS = [{"id": "blancoBrillo", "label": "Blanco brillo"}, {"id": "blancoUltramatt", "label": "Blanco ultramatt / satinado"}, {"id": "colorBrillo", "label": "Color brillo"}, {"id": "colorUltramatt", "label": "Color ultramatt / satinado"}];

/** Y los seis de la tabla de COSTADOS, que son otros: allí el color especial
 *  tiene columna propia, así que sobre un costado NO se aplica el 25 % — ya
 *  viene aplicado, y sumarlo sería cobrarlo dos veces. */
export const ACB_LACA_ACABADOS_COSTADO = [{"id": "blancoBrillo", "label": "Blanco brillo"}, {"id": "blancoMate", "label": "Blanco mate / satinado"}, {"id": "colorBrillo", "label": "Color brillo"}, {"id": "colorMate", "label": "Color mate / satinado"}, {"id": "especialBrillo", "label": "Color especial brillo"}, {"id": "especialMate", "label": "Color especial mate / satinado"}];

/** LOS MODELOS (págs. 6 y 6 bis).
 *
 *  `lineas` es una por GRUESO, porque el grueso manda en el precio: el mismo
 *  modelo a 19 y a 22 mm no vale lo mismo. Un modelo que solo tiene una línea
 *  SOLO SE FABRICA en ese grueso — pedirlo en otro no es más barato, es que no
 *  existe.
 *
 *  `tiradorAparte` es el asterisco de la pág. 6: hay que sumarle el precio del
 *  tirador (pág. 93, en `acbPuertas.js`). */
export const ACB_LACA_MODELOS = [
  { id: "ALZIRA", nombre: "ALZIRA", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ANETO", nombre: "ANETO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 10}] },
  { id: "APOLO", nombre: "APOLO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "ARIZONA", nombre: "ARIZONA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ARLES", nombre: "ARLES", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "BALTIMORE", nombre: "BALTIMORE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "BERNA", nombre: "BERNA", tiradorAparte: true, lineas: [{"grueso": 19, "grupo": 1, "recargo": 0}, {"grueso": 22, "grupo": 1, "recargo": 5}] },
  { id: "BOMBAY", nombre: "BOMBAY", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "CADAQUES", nombre: "CADAQUES", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "CALGARI", nombre: "CALGARI", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "CAMBRIDGE", nombre: "CAMBRIDGE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "CORINTIA", nombre: "CORINTIA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "DENVER", nombre: "DENVER", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "DOHA", nombre: "DOHA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "DRESDE", nombre: "DRESDE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "DUELAS", nombre: "DUELAS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "EPOCA", nombre: "EPOCA", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ESTOCOLMO_T1", nombre: "ESTOCOLMO T1", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ESTOCOLMO_T2", nombre: "ESTOCOLMO T2", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "EVEREST", nombre: "EVEREST", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 10}] },
  { id: "FLORENCIA", nombre: "FLORENCIA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 10}] },
  { id: "FLORIDA", nombre: "FLORIDA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "GANTE_TirNogal", nombre: "GANTE TirNogal", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 15}] },
  { id: "GRECIA", nombre: "GRECIA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "HANOI", nombre: "HANOI", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "KANSAS", nombre: "KANSAS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "KANSAS_Pf_Rayado", nombre: "KANSAS Pf. Rayado", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "LAREDO", nombre: "LAREDO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "LEIDEN", nombre: "LEIDEN", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 1, "recargo": 0}] },
  { id: "LIEJA", nombre: "LIEJA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "LIMA", nombre: "LIMA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MADRID", nombre: "MADRID", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 1, "recargo": 0}, {"grueso": 22, "grupo": 1, "recargo": 5}] },
  { id: "MAELLA_T1", nombre: "MAELLA T1", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MAELLA_T2", nombre: "MAELLA T2", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MALAGA", nombre: "MALAGA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 0}] },
  { id: "MALLORCA", nombre: "MALLORCA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "MANACOR", nombre: "MANACOR", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MARINA", nombre: "MARINA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MELBOURNE", nombre: "MELBOURNE", tiradorAparte: false, lineas: [{"grueso": 25, "grupo": 3, "recargo": 15}] },
  { id: "MILOS", nombre: "MILOS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "MONACO", nombre: "MONACO", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 3, "recargo": 0}, {"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "NANTES", nombre: "NANTES", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "NUBE", nombre: "NUBE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "OLIMPIA", nombre: "OLIMPIA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ONDAS_1CM", nombre: "ONDAS 1CM", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "ONDAS_2_5CM", nombre: "ONDAS 2,5CM", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "ORLANDO", nombre: "ORLANDO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ORLEANS", nombre: "ORLEANS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "OSTENDE", nombre: "OSTENDE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "OXFORD", nombre: "OXFORD", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 10}] },
  { id: "PALENCIA", nombre: "PALENCIA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "PALMA", nombre: "PALMA", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 2, "recargo": 0}, {"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "RIGA", nombre: "RIGA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "RODAS", nombre: "RODAS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ROTTERDAM", nombre: "ROTTERDAM", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 2, "recargo": 0}] },
  { id: "SADA", nombre: "SADA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "SALZBURGO", nombre: "SALZBURGO", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 2, "recargo": 0}, {"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "SILOS", nombre: "SILOS", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "TAPIES", nombre: "TAPIES", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 2, "recargo": 0}, {"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "TEVERE", nombre: "TEVERE", tiradorAparte: false, lineas: [{"grueso": 30, "grupo": 3, "recargo": 15}] },
  { id: "TRENTO", nombre: "TRENTO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "TREVISO", nombre: "TREVISO", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "TRIPOLI", nombre: "TRIPOLI", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "VANCOUVER", nombre: "VANCOUVER", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "VARESE", nombre: "VARESE", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 25}] },
  { id: "VEGA", nombre: "VEGA", tiradorAparte: false, lineas: [{"grueso": 19, "grupo": 2, "recargo": 0}, {"grueso": 22, "grupo": 2, "recargo": 5}] },
  { id: "XATIVA", nombre: "XATIVA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 0}] },
  { id: "YAKARTA", nombre: "YAKARTA", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 3, "recargo": 5}] },
  { id: "ZAGREB", nombre: "ZAGREB", tiradorAparte: false, lineas: [{"grueso": 30, "grupo": 3, "recargo": 15}] },
  { id: "ZAMORA_TirNogal", nombre: "ZAMORA TirNogal", tiradorAparte: false, lineas: [{"grueso": 22, "grupo": 2, "recargo": 15}] },
];

/** LEIDEN sale en dos grupos a la vez en la tarifa de ACB. Se toma el de la
 *  pág. 6 (la tabla de modelos, que es la que manda); la cabecera de la matriz
 *  del grupo 3 también lo lista. Son 3,59 € por frente en la casilla base, así
 *  que conviene confirmarlo con el proveedor en vez de dejarlo sin decir. */
export const ACB_LACA_MODELOS_EN_DOS_GRUPOS = {"LEIDEN": [1, 3]};

/** LAS TRES MATRICES DE GRUPO (págs. 8 a 13), en MILÍMETROS.
 *  Un alto como «138 & 173» son DOS medidas al mismo precio: por eso `altos`
 *  es una lista y no un número. */
export const ACB_LACA_MATRICES = {
  1: [
    { altos: [138, 173], anchos: [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [18.4, 18.4, 18.4, 18.4, 20.51, 20.51, 20.51, 30.76, 36.9, 41.01, 41.01, 41.01], "blancoUltramatt": [17.46, 17.46, 17.46, 17.46, 19.44, 19.44, 19.44, 29.21, 35.05, 38.95, 38.95, 38.95], "colorBrillo": [21.23, 21.24, 21.24, 21.24, 23.66, 23.66, 23.66, 35.51, 42.61, 47.36, 47.36, 47.36], "colorUltramatt": [20.18, 20.17, 20.17, 20.17, 22.48, 22.48, 22.48, 33.73, 40.48, 44.98, 44.98, 44.98]} },
    { altos: [278], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [32.37, 33.76, 33.76, 35.18, 35.18, 35.18, 41.18, 51.83, 62.5, 78.1, 93.57], "blancoUltramatt": [30.76, 32.07, 32.07, 33.41, 33.41, 33.41, 39.13, 49.26, 59.39, 74.22, 88.86], "colorBrillo": [37.37, 39.01, 39.01, 40.62, 40.62, 40.62, 47.52, 59.88, 72.22, 90.28, 108.04], "colorUltramatt": [35.52, 37.06, 37.06, 38.42, 38.42, 38.42, 45.17, 56.88, 68.58, 85.76, 102.63]} },
    { altos: [348], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [33.37, 35.58, 35.58, 37.82, 37.82, 37.82, 42.58, 54.92, 67.26], "blancoUltramatt": [31.7, 33.81, 33.81, 35.94, 35.94, 35.94, 40.45, 52.18, 63.9], "colorBrillo": [38.54, 41.11, 41.11, 43.68, 43.68, 43.68, 49.16, 63.43, 77.68], "colorUltramatt": [36.61, 39.04, 39.04, 41.5, 41.5, 41.5, 46.71, 60.25, 73.8]} },
    { altos: [418], anchos: [298, 598], precios: {"blancoBrillo": [35.58, 50.43], "blancoUltramatt": [33.81, 47.89], "colorBrillo": [41.11, 58.22], "colorUltramatt": [39.04, 55.3]} },
    { altos: [448], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [41.01, 42.03, 43.6, 44.64, 46.77, 53.08, 53.57, 74.21, 74.21], "blancoUltramatt": [38.94, 39.92, 41.43, 42.41, 44.44, 50.41, 50.89, 70.68, 70.68], "colorBrillo": [47.35, 48.56, 50.36, 51.59, 54.05, 61.28, 61.91, 85.9, 85.9], "colorUltramatt": [44.99, 46.08, 47.86, 48.98, 51.33, 58.21, 58.78, 81.61, 81.61]} },
    { altos: [558], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [41.01, 41.01, 42.03, 43.6, 44.64, 46.77, 53.08], "blancoUltramatt": [38.94, 38.94, 39.92, 41.43, 42.41, 44.44, 50.41], "colorBrillo": [47.35, 47.35, 48.56, 50.36, 51.59, 54.05, 61.28], "colorUltramatt": [44.99, 44.99, 46.08, 47.86, 48.98, 51.33, 58.21]} },
    { altos: [598], anchos: [598], precios: {"blancoBrillo": [62.51], "blancoUltramatt": [59.38], "colorBrillo": [72.21], "colorUltramatt": [68.58]} },
    { altos: [698], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [41.18, 41.18, 42.58, 44.64, 48.86, 53.08, 62.52], "blancoUltramatt": [39.13, 39.13, 40.45, 42.41, 46.44, 50.41, 59.39], "colorBrillo": [47.53, 47.53, 49.16, 51.59, 56.44, 61.28, 72.22], "colorUltramatt": [45.17, 45.17, 46.7, 48.98, 53.61, 58.21, 68.58]} },
    { altos: [798], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [61.27, 61.27, 65.91, 67.0, 72.71, 78.89, 84.33], "blancoUltramatt": [58.2, 58.2, 62.62, 63.66, 69.27, 74.98, 80.11], "colorBrillo": [70.77, 70.78, 76.13, 77.4, 84.18, 91.15, 97.38], "colorUltramatt": [67.21, 67.21, 72.32, 73.53, 79.97, 86.57, 92.52]} },
    { altos: [898], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [62.52, 62.52, 67.26, 68.36, 74.2, 80.5, 86.05], "blancoUltramatt": [59.39, 59.39, 63.9, 64.96, 70.68, 76.51, 81.75], "colorBrillo": [72.22, 72.22, 77.68, 78.97, 85.9, 93.01, 99.36], "colorUltramatt": [68.58, 68.58, 73.8, 75.03, 81.61, 88.34, 94.41]} },
    { altos: [1198, 1298], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [93.57, 93.57, 93.57, 104.57, 120.86, 120.86], "blancoUltramatt": [88.85, 88.85, 88.85, 99.35, 114.8, 114.8], "colorBrillo": [108.05, 108.05, 108.05, 120.76, 139.58, 139.58], "colorUltramatt": [102.63, 102.63, 102.63, 114.71, 132.6, 132.6]} },
    { altos: [1498, 1598], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [103.68, 109.84, 113.01, 123.07, 133.57, 148.56], "blancoUltramatt": [98.49, 104.34, 107.35, 116.91, 126.89, 141.12], "colorBrillo": [119.74, 119.74, 130.52, 142.13, 154.27, 171.57], "colorUltramatt": [113.74, 113.74, 123.99, 135.01, 146.54, 162.99]} },
  ],
  2: [
    { altos: [138, 173], anchos: [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [19.98, 19.98, 19.98, 19.98, 22.26, 22.26, 22.26, 33.39, 40.07, 44.52, 44.52, 44.52], "blancoUltramatt": [18.98, 18.98, 18.98, 18.98, 21.17, 21.17, 21.17, 31.77, 38.13, 42.36, 42.36, 42.36], "colorBrillo": [23.09, 23.09, 23.09, 23.09, 25.72, 25.72, 25.72, 38.57, 46.3, 51.44, 51.44, 51.44], "colorUltramatt": [21.93, 21.93, 21.93, 21.93, 24.42, 24.42, 24.42, 36.63, 43.95, 48.84, 48.84, 48.84]} },
    { altos: [278], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [35.18, 36.71, 36.71, 38.23, 38.23, 38.23, 44.75, 56.36, 67.97, 84.96, 101.69], "blancoUltramatt": [33.41, 34.87, 34.87, 36.33, 36.33, 36.33, 42.51, 53.52, 64.54, 80.7, 96.6], "colorBrillo": [40.63, 42.4, 42.4, 44.18, 44.18, 44.18, 51.7, 65.1, 78.49, 98.11, 117.42], "colorUltramatt": [38.61, 40.3, 40.3, 41.96, 41.96, 41.96, 49.09, 61.83, 74.57, 93.2, 111.55]} },
    { altos: [348], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [36.27, 38.67, 38.67, 41.11, 41.11, 41.11, 46.29, 59.68, 73.08], "blancoUltramatt": [34.45, 36.75, 36.75, 39.05, 39.05, 39.05, 43.95, 56.69, 69.45], "colorBrillo": [41.9, 44.68, 44.68, 47.47, 47.47, 47.47, 53.45, 68.95, 84.43], "colorUltramatt": [39.79, 42.45, 42.45, 45.1, 45.1, 45.1, 50.76, 65.49, 80.22]} },
    { altos: [418], anchos: [298, 598], precios: {"blancoBrillo": [38.67, 54.79], "blancoUltramatt": [36.75, 52.05], "colorBrillo": [44.68, 63.3], "colorUltramatt": [42.45, 60.13]} },
    { altos: [448], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [44.54, 45.69, 47.4, 48.55, 50.85, 57.67, 58.26, 80.88, 80.88], "blancoUltramatt": [42.33, 43.41, 45.04, 46.08, 48.28, 54.79, 55.3, 76.81, 76.81], "colorBrillo": [51.46, 52.75, 54.77, 56.04, 58.74, 66.63, 67.25, 93.38, 93.38], "colorUltramatt": [48.89, 50.14, 52.01, 53.26, 55.78, 63.3, 63.91, 88.71, 88.71]} },
    { altos: [558], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [44.54, 44.54, 45.69, 47.4, 48.55, 50.85, 57.67], "blancoUltramatt": [42.33, 42.33, 43.41, 45.04, 46.08, 48.28, 54.79], "colorBrillo": [51.46, 51.46, 52.75, 54.77, 56.04, 58.74, 66.63], "colorUltramatt": [48.89, 48.89, 50.14, 52.01, 53.26, 55.78, 63.3]} },
    { altos: [598], anchos: [598], precios: {"blancoBrillo": [67.95], "blancoUltramatt": [64.54], "colorBrillo": [78.49], "colorUltramatt": [74.57]} },
    { altos: [698], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [44.75, 44.75, 46.29, 48.55, 53.12, 57.67, 67.95], "blancoUltramatt": [42.51, 42.51, 43.95, 46.08, 50.45, 54.79, 64.54], "colorBrillo": [51.7, 51.7, 53.45, 56.04, 61.32, 66.63, 78.49], "colorUltramatt": [49.09, 49.09, 50.76, 53.26, 58.28, 63.3, 74.57]} },
    { altos: [798], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [66.59, 66.59, 71.62, 72.85, 79.26, 85.76, 91.66], "blancoUltramatt": [63.25, 63.25, 68.04, 69.19, 75.26, 81.49, 87.07], "colorBrillo": [76.92, 76.92, 82.75, 84.12, 91.51, 99.03, 105.84], "colorUltramatt": [73.08, 73.08, 78.62, 79.91, 86.94, 94.11, 100.56]} },
    { altos: [898], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [67.95, 67.95, 73.08, 74.34, 80.87, 87.51, 93.53], "blancoUltramatt": [64.54, 64.54, 69.43, 70.6, 76.8, 83.15, 88.85], "colorBrillo": [78.49, 78.49, 84.43, 85.84, 93.38, 101.05, 108.0], "colorUltramatt": [74.57, 74.57, 80.22, 81.54, 88.71, 96.03, 102.61]} },
    { altos: [1198, 1298], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [101.69, 101.69, 101.69, 114.07, 131.36, 131.36], "blancoUltramatt": [96.6, 96.6, 96.6, 107.98, 124.79, 124.79], "colorBrillo": [117.43, 117.43, 117.43, 131.24, 151.74, 151.74], "colorUltramatt": [111.56, 111.56, 111.56, 124.71, 144.16, 144.16]} },
    { altos: [1498, 1598], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [112.69, 119.38, 122.89, 128.66, 145.19, 161.46], "blancoUltramatt": [107.05, 113.4, 116.75, 122.23, 137.93, 153.38], "colorBrillo": [130.15, 137.88, 141.93, 148.59, 167.69, 186.49], "colorUltramatt": [123.64, 130.97, 134.8, 141.15, 159.29, 177.16]} },
  ],
  3: [
    { altos: [138, 173], anchos: [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [21.99, 21.99, 21.99, 21.99, 24.49, 24.49, 24.49, 36.74, 44.07, 48.98, 48.98, 48.98], "blancoUltramatt": [20.88, 20.88, 20.88, 20.88, 23.26, 23.26, 23.26, 34.89, 41.86, 46.53, 46.53, 46.53], "colorBrillo": [25.39, 25.39, 25.39, 25.39, 28.28, 28.28, 28.28, 42.42, 50.89, 56.57, 56.57, 56.57], "colorUltramatt": [24.12, 24.12, 24.12, 24.12, 26.88, 26.88, 26.88, 40.28, 48.5, 53.74, 53.74, 53.74]} },
    { altos: [278], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], precios: {"blancoBrillo": [38.69, 40.38, 40.38, 42.08, 42.08, 42.08, 49.24, 61.98, 74.75, 93.45, 111.83], "blancoUltramatt": [36.77, 38.38, 38.38, 39.97, 39.97, 39.97, 46.75, 58.88, 71.02, 88.77, 106.25], "colorBrillo": [44.68, 46.63, 46.63, 48.61, 48.61, 48.61, 56.85, 71.59, 86.34, 107.92, 129.21], "colorUltramatt": [42.45, 44.29, 44.29, 46.15, 46.15, 46.15, 54.02, 68.01, 82.0, 102.49, 122.71]} },
    { altos: [348], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [39.9, 42.56, 42.56, 45.21, 45.21, 45.21, 50.91, 65.67, 80.41], "blancoUltramatt": [37.9, 40.43, 40.43, 42.95, 42.95, 42.95, 48.34, 62.37, 76.4], "colorBrillo": [46.06, 49.13, 49.13, 52.2, 52.2, 52.2, 58.8, 75.84, 92.88], "colorUltramatt": [43.76, 46.68, 46.68, 49.62, 49.62, 49.62, 55.84, 72.05, 88.25]} },
    { altos: [418], anchos: [298, 598], precios: {"blancoBrillo": [42.56, 60.28], "blancoUltramatt": [40.43, 57.27], "colorBrillo": [49.13, 69.63], "colorUltramatt": [46.68, 66.13]} },
    { altos: [448], anchos: [298, 348, 398, 448, 498, 598, 698, 798, 898], precios: {"blancoBrillo": [49.01, 50.68, 52.16, 53.37, 55.94, 63.46, 70.09, 88.93, 88.93], "blancoUltramatt": [46.56, 47.76, 49.53, 50.72, 53.12, 60.28, 66.6, 84.48, 84.48], "colorBrillo": [56.61, 58.04, 60.23, 61.68, 64.59, 73.3, 80.98, 102.7, 102.7], "colorUltramatt": [53.76, 55.12, 57.2, 58.58, 61.37, 69.61, 76.93, 97.6, 97.6]} },
    { altos: [558], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [49.01, 49.01, 50.68, 52.16, 53.37, 55.94, 63.46], "blancoUltramatt": [46.56, 46.56, 47.76, 49.53, 50.72, 53.12, 60.28], "colorBrillo": [56.61, 56.61, 58.04, 60.23, 61.68, 64.59, 73.3], "colorUltramatt": [53.76, 53.76, 55.12, 57.2, 58.58, 61.37, 69.61]} },
    { altos: [598], anchos: [598], precios: {"blancoBrillo": [74.75], "blancoUltramatt": [71.02], "colorBrillo": [86.34], "colorUltramatt": [82.02]} },
    { altos: [698], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [49.24, 49.24, 50.91, 53.37, 58.4, 63.46, 74.75], "blancoUltramatt": [46.75, 46.75, 48.34, 50.7, 55.5, 60.28, 71.02], "colorBrillo": [56.85, 56.85, 58.8, 61.68, 67.49, 73.3, 86.34], "colorUltramatt": [54.02, 54.02, 55.84, 58.58, 64.11, 69.61, 82.02]} },
    { altos: [798], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [73.26, 73.26, 78.8, 80.11, 87.15, 94.32, 100.8], "blancoUltramatt": [69.6, 69.6, 74.88, 76.1, 82.8, 89.63, 95.77], "colorBrillo": [84.61, 84.61, 91.02, 92.52, 100.64, 108.96, 116.44], "colorUltramatt": [80.38, 80.38, 86.48, 87.9, 95.64, 103.5, 110.63]} },
    { altos: [898], anchos: [248, 298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [74.75, 74.75, 80.41, 81.75, 88.93, 96.24, 102.86], "blancoUltramatt": [71.02, 71.02, 76.4, 77.66, 84.49, 91.46, 97.72], "colorBrillo": [86.34, 86.34, 92.88, 94.41, 102.7, 111.18, 118.81], "colorUltramatt": [82.02, 82.02, 88.25, 89.7, 97.59, 105.61, 112.89]} },
    { altos: [1198, 1298], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [111.84, 111.84, 111.84, 124.99, 144.5, 144.5], "blancoUltramatt": [106.24, 106.24, 106.24, 118.77, 137.27, 137.27], "colorBrillo": [129.21, 129.21, 129.21, 144.4, 166.89, 166.89], "colorUltramatt": [122.72, 122.72, 122.72, 137.16, 158.54, 158.54]} },
    { altos: [1498, 1598], anchos: [298, 348, 398, 448, 498, 598], precios: {"blancoBrillo": [123.99, 131.33, 135.13, 147.33, 159.7, 177.62], "blancoUltramatt": [117.78, 124.76, 128.37, 139.96, 151.71, 168.74], "colorBrillo": [143.2, 151.67, 156.07, 170.15, 184.44, 205.12], "colorUltramatt": [136.02, 144.07, 148.25, 161.64, 175.2, 194.85]} },
  ],
};

/** LOS COLORES (pág. 7).
 *
 *  Los ESPECIALES no son «otro color»: se tarifan sobre el precio de BLANCO
 *  con un 25 % encima, NO sobre el de color. Con el blanco brillo del grupo 1
 *  en 18,40 €, un microarenado sale a 23,00 € y no a 26,54 €, que es lo que
 *  daría aplicárselo a la columna de color. */
export const ACB_LACA_COLORES = {"estandar": ["AGUA MARINA", "ALGA", "ALUMINIO", "AMAPOLA", "ANTARTIDA", "ANTRACITA", "ARDILLA", "ARENA", "ARIDO", "AYURE", "AZUL ARMONIA", "AZUL CARIBE", "AZUL OXFORD", "AZUL REAL", "BEIGE", "BEIGE GRISACEO", "BLANCO", "BLANCO ROTO", "BLANCO RUSTICO", "BOSQUE", "BURDEOS", "CAMEL", "CANELA", "CARIOCA", "CASTAÑO", "CAVA", "CENIZA", "CEREZA", "CHOCOLATE", "CIELO", "COBRE", "COCO", "CORZO", "CRISTALINO", "CURRY", "DESIERTO", "DORADO", "EGEO", "GOLD", "GRAFITO", "GRANATE", "GREEN", "GRIS", "GRIS NEUTRO", "GRIS PERLA", "GRIS PLOMO", "GRIS TAMAKI", "GRUS VITBER", "HUESO Nº10", "HUESO Nº8", "LAGO", "LANDALO", "LINO", "LONDON GREY", "LUNA", "MAGNOLIA", "MARENGO", "MARFIL", "MARTE", "MEDITERRANEO", "MENTA", "MERENGUE", "MOSTAZA", "MUSGO", "NEGRO", "NIGU", "NUBE", "NÍSPERO", "OCEANO", "OLIVE", "ORO", "OTOÑO", "PAPER CREAM", "PASTEL", "PERGAMON Nº1", "PIEDRA ARENA", "PIEDRA BEIGE", "PIEDRA GRAFITO", "PIEDRA GRIS", "PIGEON", "PISTACHO", "PIZARRA", "PLATA", "PLOMO", "PORCELANA", "PRIMAVERA", "RIOJA", "ROJO", "ROJO TINTO", "ROSA CARAMELO", "SAHARA", "SILICE", "SMOKE", "SOMBRA", "STONE", "TERRA", "TERRACOTA", "TERROSA", "TEXAS", "TINTO", "TITANIO", "TOFFE", "TOPO", "TREBOL", "TURQUESA", "VANILA", "VERDE AZULADO", "VERDE CLARO", "VERDE FONTANA", "VIOLETA", "VISON", "VULCANO", "YESO"], "especiales": ["MICROARENADO BONE", "MICROARENADO DARK GREEN", "MICROARENADO DESERT", "MICROARENADO GREY", "MICROARENADO IGNEO", "MICROARENADO LAVA", "MICROARENADO SAND", "MICROARENADO SIENA"], "decoraciones": [{"nombre": "ARISTA VIVA", "pct": 5}, {"nombre": "FILO CROMADO", "pct": 10}, {"nombre": "FILO ORO", "pct": 10}, {"nombre": "INOX METAL COBRE", "pct": 18}, {"nombre": "INOX METAL PLATA", "pct": 18}, {"nombre": "METALIZADO", "pct": 10}, {"nombre": "METAL ACERO", "pct": 18}, {"nombre": "METAL ORO", "pct": 18}, {"nombre": "PATINADO", "pct": 10}]};

/** COMPLEMENTOS por PIEZA (pág. 14): cornisas, portaluces, zócalo de 15,
 *  paneles, botelleros y campanas. Los precios van en el orden de
 *  `ACB_LACA_ACABADOS`. */
export const ACB_LACA_COMPLEMENTOS = [{"nombre": "CORNISA PLANA", "precios": [67.8, 64.4, 78.29, 74.39]}, {"nombre": "CORNISA REDONDA", "precios": [65.3, 62.04, 75.42, 71.63]}, {"nombre": "CORNISA DISEÑO", "precios": [91.38, 86.82, 105.55, 100.26]}, {"nombre": "PORTALUZ", "precios": [56.84, 54.0, 65.67, 62.38]}, {"nombre": "PORTALUZ DISEÑO", "precios": [81.71, 77.59, 94.37, 89.65]}, {"nombre": "ZOCALO DE 15", "precios": [43.6, 41.43, 50.36, 47.86]}, {"nombre": "FRENTE HORNO 75X598", "precios": [10.34, 9.84, 11.95, 11.36]}, {"nombre": "REGLETA 698X98", "precios": [10.92, 10.38, 12.61, 11.97]}, {"nombre": "REGLETA 900X98", "precios": [14.49, 13.76, 16.73, 15.87]}, {"nombre": "REGLETA 1940X98", "precios": [31.24, 29.67, 36.09, 34.27]}, {"nombre": "COSTADO 2440X600X19", "precios": [125.32, 119.05, 144.73, 137.5]}, {"nombre": "COSTADO 2 CARAS 2440X600X19", "precios": [164.73, 156.49, 190.24, 180.75]}, {"nombre": "PANEL 2440X600X4", "precios": [54.5, 51.76, 62.95, 59.77]}, {"nombre": "DECORATIVO 3B 700X300X300", "precios": [81.08, 77.01, 93.64, 88.95]}, {"nombre": "DECORATIVO 4B 900X300X300", "precios": [105.58, 100.31, 121.95, 115.83]}, {"nombre": "BOTELLERO 5B 700X300X300", "precios": [98.29, 93.36, 113.51, 107.83]}, {"nombre": "BOTELLERO 6B 900X300X300", "precios": [122.66, 116.54, 141.68, 134.62]}, {"nombre": "CAMPANA TRAPECIO", "precios": [541.41, 514.34, 625.35, 594.04]}, {"nombre": "CAMPANA DISEÑO A", "precios": [912.28, 866.67, 1101.59, 1046.42]}, {"nombre": "CAMPANA DISEÑO B", "precios": [709.96, 674.27, 819.76, 782.51]}, {"nombre": "CAMPANA DISEÑO C", "precios": [709.96, 674.27, 819.76, 782.51]}, {"nombre": "CAMPANA DISEÑO D", "precios": [709.96, 674.27, 819.76, 782.51]}, {"nombre": "CAMPANA DISEÑO E", "precios": [709.96, 674.27, 819.76, 782.51]}, {"nombre": "CAMPANA DISEÑO F", "precios": [892.01, 847.41, 1077.1, 1023.23]}];

/** Regletas y columnas de diseño (pág. 15). Estas SOLO se hacen en ultramatt,
 *  así que llevan dos precios y no cuatro: [blanco, color]. */
export const ACB_LACA_DISENO = [{"nombre": "REGLETA DISEÑO Nº 3 700X98 PIRAMIDE", "precios": [23.03, 31.46]}, {"nombre": "REGLETA DISEÑO Nº 3 900X98 PIRAMIDE", "precios": [29.61, 40.46]}, {"nombre": "REGLETA DISEÑO Nº 3 1940X98 PIRAMIDE", "precios": [48.34, 66.09]}, {"nombre": "COLUMNA DISEÑO CLÁSICO 700", "precios": [89.75, 106.22]}, {"nombre": "COLUMNA DISEÑO CLÁSICO 900", "precios": [106.45, 125.97]}, {"nombre": "COLUMNA DISEÑO CLÁSICO 1940", "precios": [266.62, 315.54]}];

/** Curvas para terminal (pág. 15), por alto. OJO: en las dos tablas CON
 *  MOLDURA la tarifa invierte brillo y ultramatt —el ultramatt cuesta más—, y
 *  lo hace en las nueve filas, así que no es un dígito suelto. */
export const ACB_LACA_CURVAS = [{"grupo": "CURVAS PARA TERMINAL DISEÑO LISO", "filas": [{"alto": "ALTO HASTA 70 CM", "precios": [148.71, 141.27, 171.76, 163.17]}, {"alto": "ALTO HASTA 90 CM", "precios": [182.39, 173.27, 210.66, 200.13]}, {"alto": "ALTO HASTA 130 CM", "precios": [241.55, 229.47, 278.99, 265.04]}, {"alto": "ALTO HASTA 200 CM", "precios": [351.87, 334.28, 406.42, 386.09]}]}, {"grupo": "CURVAS PARA TERMINAL DISEÑO CON MOLDURA", "filas": [{"alto": "ALTO HASTA 70 CM", "precios": [257.55, 269.66, 285.78, 310.03]}, {"alto": "ALTO HASTA 90 CM", "precios": [293.35, 307.78, 325.85, 353.57]}, {"alto": "ALTO HASTA 130 CM", "precios": [344.11, 360.73, 382.34, 414.97]}, {"alto": "ALTO HASTA 150 CM", "precios": [396.06, 415.31, 440.34, 478.0]}, {"alto": "ALTO HASTA 200 CM", "precios": [446.73, 468.86, 497.25, 539.86]}]}, {"grupo": "CURVAS PARA TERMINAL DISEÑO CON MOLDURA PARA ISLA DE 90 DE ANCHO (2 PUERTAS)", "filas": [{"alto": "ALTO HASTA 70 CM", "precios": [285.26, 296.49, 302.64, 336.65]}, {"alto": "ALTO HASTA 90 CM", "precios": [320.15, 334.46, 351.71, 380.58]}]}];

/** Muebles y puertas RETRO (pág. 15). */
export const ACB_LACA_RETRO = [{"nombre": "MUEBLE RETRO (ALTO) 700", "precios": [242.78, 230.64, 280.41, 266.39]}, {"nombre": "MUEBLE RETRO (BAJO) 700", "precios": [351.11, 333.55, 405.53, 385.25]}, {"nombre": "PUERTA RETRO 700X600", "precios": [70.04, 66.54, 80.89, 76.85]}, {"nombre": "MUEBLE RETRO (ALTO) 900", "precios": [265.83, 252.54, 307.03, 291.68]}, {"nombre": "PUERTA RETRO 900X600", "precios": [96.34, 91.52, 266.79, 253.45]}];

/** COSTADOS (pág. 16), por SUPERFICIE en cm². Seis columnas, en el orden de
 *  `ACB_LACA_ACABADOS_COSTADO`. */
export const ACB_LACA_COSTADOS = {"unaCara": [{"hasta": "HASTA 2000", "precios": [21.07, 20.02, 24.33, 23.11, 26.34, 25.02]}, {"hasta": "HASTA 2500", "precios": [26.29, 24.97, 30.39, 28.84, 32.89, 31.24]}, {"hasta": "HASTA 3000", "precios": [31.37, 29.97, 36.44, 34.6, 39.45, 37.47]}, {"hasta": "HASTA 3500", "precios": [36.88, 35.04, 42.59, 40.48, 46.1, 43.79]}, {"hasta": "HASTA 4000", "precios": [42.15, 40.04, 48.67, 46.27, 52.69, 50.07]}, {"hasta": "HASTA 4500", "precios": [47.37, 45.02, 54.72, 52.0, 59.23, 56.27]}, {"hasta": "HASTA 5000", "precios": [52.69, 50.07, 60.82, 57.81, 65.85, 62.56]}, {"hasta": "HASTA 5500", "precios": [57.93, 55.02, 66.9, 63.57, 72.41, 68.79]}, {"hasta": "HASTA 6000", "precios": [63.15, 59.99, 72.93, 69.3, 78.96, 75.01]}, {"hasta": "HASTA 6500", "precios": [68.42, 65.01, 79.03, 75.09, 85.53, 81.26]}, {"hasta": "HASTA 7000", "precios": [73.71, 70.01, 85.13, 80.87, 92.14, 87.51]}, {"hasta": "HASTA 7500", "precios": [79.01, 75.06, 91.26, 86.68, 98.76, 93.81]}, {"hasta": "HASTA 8000", "precios": [84.25, 80.06, 97.31, 92.46, 105.33, 100.06]}, {"hasta": "HASTA 8500", "precios": [90.18, 85.65, 104.12, 98.93, 112.73, 107.07]}, {"hasta": "HASTA 9000", "precios": [94.79, 90.03, 109.47, 104.0, 118.49, 112.55]}, {"hasta": "HASTA 9500", "precios": [100.03, 95.03, 115.52, 109.76, 125.03, 118.78]}, {"hasta": "HASTA 10000", "precios": [105.3, 100.03, 121.62, 115.54, 131.64, 125.05]}, {"hasta": "HASTA 10500", "precios": [110.62, 105.08, 127.79, 121.35, 138.26, 131.35]}, {"hasta": "DE 11000 A 14640", "precios": [125.32, 119.05, 144.73, 137.5, 156.64, 148.82]}], "dosCaras": [{"hasta": "HASTA 2000", "precios": [27.64, 26.27, 31.93, 30.36, 34.55, 32.84]}, {"hasta": "HASTA 2500", "precios": [34.58, 32.86, 39.94, 37.96, 43.23, 41.05]}, {"hasta": "HASTA 3000", "precios": [41.49, 39.43, 47.91, 45.51, 51.85, 49.26]}, {"hasta": "HASTA 3500", "precios": [48.42, 46.0, 55.95, 53.13, 60.53, 57.49]}, {"hasta": "HASTA 4000", "precios": [55.33, 52.54, 63.91, 60.72, 69.18, 65.7]}, {"hasta": "HASTA 4500", "precios": [62.27, 59.16, 71.92, 68.32, 77.83, 73.93]}, {"hasta": "HASTA 5000", "precios": [69.18, 65.7, 79.89, 75.89, 82.7, 82.14]}, {"hasta": "HASTA 5500", "precios": [76.08, 72.27, 87.88, 83.47, 95.08, 90.35]}, {"hasta": "HASTA 6000", "precios": [82.98, 78.84, 95.84, 91.06, 103.73, 98.56]}, {"hasta": "HASTA 6500", "precios": [89.91, 85.43, 103.86, 98.66, 112.38, 106.8]}, {"hasta": "HASTA 7000", "precios": [96.85, 91.99, 111.87, 106.28, 121.06, 115.03]}, {"hasta": "HASTA 7500", "precios": [103.78, 98.59, 119.86, 113.88, 129.73, 123.07]}, {"hasta": "HASTA 8000", "precios": [110.67, 105.13, 127.82, 121.43, 138.34, 131.4]}, {"hasta": "HASTA 8500", "precios": [117.58, 111.67, 135.79, 129.0, 146.96, 139.61]}, {"hasta": "HASTA 9000", "precios": [124.49, 118.29, 143.8, 136.6, 155.66, 147.84]}, {"hasta": "HASTA 9500", "precios": [131.4, 124.83, 151.76, 144.17, 164.26, 156.05]}, {"hasta": "HASTA 10000", "precios": [140.12, 133.12, 161.84, 153.75, 175.14, 166.39]}, {"hasta": "HASTA 10500", "precios": [145.25, 113.58, 167.74, 159.36, 181.56, 172.5]}, {"hasta": "DE 11000 A 14640", "precios": [164.73, 156.49, 190.24, 180.75, 205.9, 195.6]}]};

/** Los recargos del costado, escritos donde se usan. */
export const ACB_LACA_COSTADO_22MM_PCT = 0.1;
export const ACB_LACA_COSTADO_30MM_PCT = 0.25;
export const ACB_LACA_COSTADO_ALIGERADO_PCT = 0.5;
export const ACB_LACA_COSTADO_ATAMBORADO_M2 = 304.19;

/** Y los del acabado (pág. 7). */
export const ACB_LACA_COLOR_ESPECIAL_PCT = 0.25;
export const ACB_LACA_XOLID_PCT = 0.15;
export const ACB_LACA_JUNQUILLOS_VITRINA = 10.88;
export const ACB_LACA_PANEL_MUESTRAS = 16.32;

/** «El precio para medidas especiales será igual al precio de la medida
 *  inmediata superior» (pág. 7). NO SE INTERPOLA nunca: se sube al escalón
 *  siguiente. Interpolar daría un precio que ACB no factura. */
export const ACB_LACA_MEDIDA_ESPECIAL = "sube a la medida inmediata superior";

/** Los gruesos en los que ACB fabrica ese modelo. Lista vacía si el modelo no
 *  existe — que es distinto de que se fabrique en cualquiera. */
export const gruesosDeModeloACBLaca = (modelo) => {
  const m = ACB_LACA_MODELOS.find((x) => x.id === modelo || x.nombre === modelo);
  return m ? m.lineas.map((l) => l.grueso) : [];
};

/** El grupo y el recargo de un modelo EN UN GRUESO CONCRETO. `null` cuando ACB
 *  no lo fabrica así: devolver la primera línea que hubiera sería tarifar un
 *  frente de 22 mm al precio del de 19 sin dar ningún error. */
export const lineaDeModeloACBLaca = (modelo, grueso) => {
  const m = ACB_LACA_MODELOS.find((x) => x.id === modelo || x.nombre === modelo);
  if (!m) return null;
  return m.lineas.find((l) => l.grueso === Number(grueso)) || null;
};

/** El precio de tarifa del grupo, sin recargos. `null` si ACB no fabrica esa
 *  medida — que es distinto de que valga cero (CLAUDE.md, regla 7). */
export const precioBaseLacaACB = (grupo, acabado, alto, ancho) => {
  const bloques = ACB_LACA_MATRICES[Number(grupo)];
  if (!bloques) return null;
  const a = Number(alto), w = Number(ancho);
  const b = bloques.find((x) => x.altos.includes(a));
  if (!b) return null;
  const i = b.anchos.indexOf(w);
  if (i < 0) return null;
  const col = b.precios[acabado];
  return col && col[i] != null ? col[i] : null;
};

/** EL PRECIO DE UN FRENTE DE LACA, con todo lo que lleva encima.
 *
 *  Devuelve `null` en cuanto falta un dato — modelo que no existe, grueso que
 *  no se fabrica, medida que no está en la matriz. Nunca un número aproximado:
 *  un precio inventado no da ningún error, sale en el presupuesto.
 *
 *  EL COLOR ESPECIAL SE CALCULA SOBRE BLANCO, no sobre color: lo dice la
 *  pág. 7 y cambia el resultado. Y el XOLID va «sobre tarifa mate», así que
 *  fuerza la columna ultramatt.
 *
 *  Los recargos son todos multiplicativos, así que el orden en que se apliquen
 *  da lo mismo. Eso no es casualidad ni pereza: la tarifa no dice en qué orden
 *  van, y con sumas SÍ importaría — habría que elegir un orden que el PDF no
 *  respalda. */
export const precioLacaACB = (modelo, grueso, acabado, alto, ancho, opciones) => {
  const o = opciones || {};
  const linea = lineaDeModeloACBLaca(modelo, grueso);
  if (!linea) return null;

  // Colores especiales y XOLID mandan sobre la columna que se pida.
  let col = acabado;
  if (o.colorEspecial) col = acabado === 'colorBrillo' || acabado === 'blancoBrillo'
    ? 'blancoBrillo' : 'blancoUltramatt';
  if (o.xolid) col = col === 'colorBrillo' || col === 'colorUltramatt'
    ? 'colorUltramatt' : 'blancoUltramatt';

  const base = precioBaseLacaACB(linea.grupo, col, alto, ancho);
  if (base == null) return null;

  let p = base * (1 + linea.recargo / 100);
  if (o.colorEspecial) p *= 1 + ACB_LACA_COLOR_ESPECIAL_PCT;
  if (o.xolid) p *= 1 + ACB_LACA_XOLID_PCT;
  const dec = Number(o.decoracionPct);
  if (Number.isFinite(dec) && dec > 0) p *= 1 + dec / 100;
  return Math.round(p * 100) / 100;
};

/** El escalón de costado que le toca a una superficie en cm². Sube SIEMPRE al
 *  inmediato superior (pág. 7); por encima del último tramo devuelve `null`,
 *  porque ACB no lo fabrica y estirar el último precio sería inventarlo. */
export const tramoCostadoACBLaca = (cara, cm2) => {
  const tabla = ACB_LACA_COSTADOS[cara];
  if (!tabla) return null;
  const s = Number(cm2);
  if (!Number.isFinite(s) || s <= 0) return null;
  for (const t of tabla) {
    const tope = Number(String(t.hasta).match(/(\d+)\s*$/)[1]);
    if (s <= tope) return t;
  }
  return null;
};
