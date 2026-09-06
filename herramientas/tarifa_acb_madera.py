# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Genera frontend/src/data/acbMadera.js desde la tarifa ACB DE MADERA 2026.

Transcrita del PDF oficial «TARIFA GRUPO ACB 26 V.0526165», páginas 17 a 36.
Es la tercera y última colección de ACB PUERTAS, después del canteado y la
laca.

LA MADERA TIENE UNA VUELTA MÁS QUE LA LACA. Allí el grueso decidía el grupo;
aquí lo decide la CHAPA:

    precio = matriz(GRUPO, acabado, alto, ancho)
             × (1 + recargo del modelo)
             × (1 + recargo de la chapa)

Un MADRID en fresno es GRUPO 1 y en abeto tricapa es GRUPO 7 — otra matriz
entera, no un porcentaje. Y encima, la chapa lleva su propio recargo: NOGAL
+10 %, ROBLE NUDOS +15 %, en TODOS los grupos (pág. 18).

Se VALIDA antes de emitir nada.
"""
import json, os, sys

COLECCION = "madera"

# ── LAS CHAPAS, Y LO QUE CUESTAN (pág. 18 y el pie de cada matriz) ─────────
#
# «MODELOS FABRICADOS EN NOGAL, INCREMENTAN +10%» · «EN ROBLE NUDOS, +15%».
# El recargo es de la CHAPA y va en todos los grupos: no es una nota de una
# página suelta, está repetido al pie de las catorce páginas de matriz.
CHAPAS = [
    ("fresno",      "Fresno",        0),
    ("roble",       "Roble",         0),
    ("nogal",       "Nogal",        10),
    ("robleNudos",  "Roble nudos",  15),
    ("alder",       "Alder",         0),
    ("abeto",       "Abeto tricapa", 0),
]

# ── LOS MODELOS (págs. 19 y 19 bis) ───────────────────────────────────────
#
# (nombre, [(chapas, grupo, recargo)], antiguo)
#
# LA CHAPA PUEDE CAMBIAR EL GRUPO, no solo el recargo. MADRID en abeto tricapa
# es GRUPO 7 y en fresno/nogal/roble es GRUPO 1: dos matrices distintas. Igual
# PALENCIA y PALMA (7 +15 % contra 3) y VEGA (7 +10 % contra 2). Por eso cada
# línea lleva SU lista de chapas, y no hay una lista de chapas por modelo con
# un grupo único al lado — eso tarifaría el abeto al precio del fresno.
#
# El grupo está cotejado con DOS fuentes de la propia tarifa: la tabla de
# modelos de la pág. 19 y la cabecera de cada matriz (págs. 21 a 34).
MODELOS = [
    ("ANDROS",                        [(["fresno","roble"], 4, 0)], False),
    ("BALTIMORE",                     [(["fresno","roble"], 6, 0)], False),
    ("BARBADOS",                      [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("CADAQUÉS",                      [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("CALABRIA 8-10 MARCO MACIZO",    [(["alder","fresno","roble","robleNudos"], 4, 0)], False),
    ("CALABRIA 8-10 MARCO RECHAPADO", [(["fresno","nogal","roble","robleNudos"], 5, 0)], False),
    ("COPENHAGUE",                    [(["fresno","roble","robleNudos"], 4, 0)], False),
    ("CORINTIA",                      [(["fresno","roble","robleNudos"], 6, 0)], False),
    ("DENVER",                        [(["fresno","roble","robleNudos"], 6, 0)], False),
    ("DUELAS",                        [(["abeto"], 7, 20)], False),
    ("DUELAS MACIZA",                 [(["fresno","roble"], 6, 30)], False),
    ("DUELAS RECHAPADA",              [(["fresno","nogal","roble","robleNudos"], 1, 20)], False),
    ("ÉVORA",                         [(["fresno","roble"], 4, 0)], False),
    ("ESTOCOLMO",                     [(["fresno","nogal","roble","robleNudos"], 6, 10)], False),
    ("FLORIDA",                       [(["fresno","roble"], 6, 0)], False),
    ("GRECIA",                        [(["fresno","roble","robleNudos"], 6, 0)], False),
    ("HANOI",                         [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("KANSAS",                        [(["fresno","roble","robleNudos"], 6, 0)], False),
    ("LAREDO",                        [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("LIMA",                          [(["fresno","nogal","roble","robleNudos"], 4, 0)], False),
    ("MADRID",                        [(["abeto"], 7, 0),
                                       (["fresno","nogal","roble","robleNudos"], 1, 0)], False),
    ("MARINA",                        [(["fresno","roble"], 6, 0)], False),
    ("MILÁN",                         [(["fresno","roble"], 4, 0)], False),
    ("MELBOURNE",                     [(["fresno","roble"], 6, 10)], False),
    ("MUNICH",                        [(["fresno","nogal","roble","robleNudos"], 6, 10)], False),
    ("NANTES",                        [(["fresno","roble"], 6, 10)], False),
    ("NIZA",                          [(["fresno","roble","robleNudos"], 4, 0)], False),
    ("NUBE",                          [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("ONDAS",                         [(["abeto"], 7, 20)], False),
    ("ORLANDO",                       [(["fresno","roble"], 6, 0)], False),
    ("PALENCIA",                      [(["abeto"], 7, 15),
                                       (["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("PALMA",                         [(["abeto"], 7, 15),
                                       (["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("RODAS",                         [(["fresno","roble","robleNudos"], 6, 0)], False),
    ("ROTTERDAM",                     [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("SALZBURGO",                     [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("SAN REMO",                      [(["fresno","roble"], 6, 10)], False),
    ("TEVERE",                        [(["fresno","nogal","roble","robleNudos"], 6, 10)], False),
    ("TRENTO",                        [(["fresno","nogal","roble","robleNudos"], 4, 0)], False),
    ("TRÍPOLI",                       [(["fresno","nogal","roble","robleNudos"], 3, 0)], False),
    ("YAKARTA",                       [(["fresno","roble"], 6, 10)], False),
    ("VEGA",                          [(["abeto"], 7, 10),
                                       (["fresno","nogal","roble","robleNudos"], 2, 0)], False),
]

# MODELOS ANTIGUOS (pág. 19 bis). Siguen en tarifa y hay cocinas montadas con
# ellos, así que se pueden pedir; lo que NO trae la tarifa es su lista de
# chapas. Eso se deja VACÍO y marcado, no se rellena con la lista de otro
# modelo parecido — inventarse en qué maderas se fabrica una puerta es
# exactamente lo que no se hace (CLAUDE.md, regla 7).
#
# Los diez MACIZOS llevan un +30 % que en el PDF va en la CABECERA del bloque,
# no en cada fila: se escribe en cada uno para que no dependa de que alguien
# se acuerde de mirar el título.
ANTIGUOS = [
    (["ASTURIAS", "BERLIN", "CAMBRIDGE", "ESPINOSA MARINO", "OVIEDO",
      "PENAGOS", "VERONA"], 3, 0),
    (["CIES", "CORCEGA", "FLOR MEMBRANA", "ROMA RECHAPADA", "SEUL"], 6, 0),
    (["ARZUA", "CALABRIA MARINO", "COIMBRA", "EGABRO", "NASTUR", "PARIS",
      "SEGURA"], 4, 0),
    (["ANETO"], 4, 30),
    (["BARI", "BERLIN MACIZA", "BOSTON", "LIVORNO", "OPORTO", "ORENSE",
      "PISA", "TURIN MACIZA", "VENECIA", "ITACA"], 6, 30),
]
for nombres, grupo, recargo in ANTIGUOS:
    for n in nombres:
        MODELOS.append((n, [([], grupo, recargo)], True))
MODELOS.sort(key=lambda m: m[0])

# ── LOS ACABADOS: las tres columnas de precio ─────────────────────────────
ACABADOS = [
    ("crudo",  "Crudo"),
    ("grupoB", "Grupo B"),
    ("grupoC", "Grupo C"),
]

# La TABLA DE ACABADOS de la pág. 20: qué códigos entran en cada grupo. No es
# decorativo — es lo que dice si el acabado que pide el cliente se cobra por la
# columna B o por la C, que son precios distintos.
#
# OJO: en ROBLE NUDOS la tarifa salta del H03 al H05. El H04 NO ESTÁ en el PDF.
# Se copia el salto tal cual: rellenarlo sería inventarse una referencia.
ACABADOS_CARTA = {
    "grupoB": {
        "Nogal":     ["N1", "N2", "N6", "N7", "N8", "N9"],
        "Roble":     ["T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10",
                      "T11", "T12", "T13"],
        "Eucalipto": ["E1", "E2"],
    },
    "grupoC": {
        "Fresno": ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08",
                   "F09", "F10", "F11", "F12", "F13", "F14", "F15", "F16",
                   "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24",
                   "F25", "F26", "F27", "F28", "F29"],
        "Roble":  ["P01", "P02"],
        "Roble nudos": ["H01", "H02", "H03", "H05", "H06", "H07"],
    },
}

# ── LAS SIETE MATRICES DE GRUPO (págs. 21 a 34) ────────────────────────────
#
# (altos, anchos, {acabado: [precios en el mismo orden que los anchos]}).
#
# EL GRUPO 7 (abeto tricapa) SOLO TIENE COLUMNA DE CRUDO: sus acabados son
# recargos sobre ella, no columnas. Por eso la matriz lleva las claves que
# tiene y no cuatro rellenadas con lo que sea.
#
# La rejilla es la misma en los siete: 82 casillas, 11 bloques de alto. NO
# lleva el bloque de 418 que sí tienen el canteado y la laca.
#
# DOS CASILLAS SE LEYERON A OJO EN EL PDF a 400 dpi, porque al extraer el
# texto sus dos precios salían pegados en un solo número y la fila se caía
# entera: el grupo 3 de 278x498 (50,04 · 59,61 · 62,00) y el grupo 5 de
# 898x398 (58,32 · 71,69 · 74,56). Se comprobaron celda a celda contra la
# página impresa.
MATRICES = {
    1: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [14.62,14.62,15.71,16.88,18.85,20.49,24.21,31.42,33.78,37.70,41.00,48.43],
            'grupoB': [16.24,16.24,17.46,18.76,20.94,22.77,26.90,34.91,37.53,41.89,45.56,53.81],
            'grupoC': [16.89,16.89,18.15,19.51,21.78,23.68,27.98,36.31,39.03,43.57,47.38,55.96],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [21.44,26.46,26.46,31.52,31.52,31.52,35.42,42.51,46.55,55.86,61.45],
            'grupoB': [23.82,29.40,29.40,35.02,35.02,35.02,39.36,47.23,51.73,62.07,68.28],
            'grupoC': [24.77,30.58,30.58,36.42,36.42,36.42,40.93,49.12,53.80,64.55,71.01],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [22.04,29.66,29.66,37.28,37.28,37.28,39.75,47.70,52.35],
            'grupoB': [24.49,32.95,32.95,41.43,41.43,41.43,44.17,53.00,58.16],
            'grupoC': [25.47,34.27,34.27,43.08,43.08,43.08,45.93,55.12,60.49],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [32.59,36.57,40.75,44.84,48.80,56.96,62.65,63.98,63.98],
            'grupoB': [36.22,40.63,45.27,49.82,54.23,63.28,69.61,71.08,71.08],
            'grupoC': [37.66,42.26,47.08,51.82,56.40,65.82,72.40,73.93,73.93],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [35.42,35.42,39.75,44.29,48.74,53.05,61.91],
            'grupoB': [39.36,39.36,44.17,49.21,54.15,58.94,68.79],
            'grupoC': [40.93,40.93,45.93,51.18,56.32,61.30,71.55],
        }),
        ([598], [598], {
            'crudo':  [61.91],
            'grupoB': [68.79],
            'grupoC': [71.55],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [35.42,35.42,39.75,44.29,48.74,53.05,61.91],
            'grupoB': [39.36,39.36,44.17,49.21,54.15,58.94,68.79],
            'grupoC': [40.93,40.93,45.93,51.18,56.32,61.30,71.55],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [46.55,46.55,52.35,58.21,63.98,69.74,81.38],
            'grupoB': [51.73,51.73,58.16,64.68,71.08,77.49,90.43],
            'grupoC': [53.80,53.80,60.49,67.26,73.93,80.59,94.04],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [46.55,46.55,52.35,58.21,63.98,69.74,81.38],
            'grupoB': [51.73,51.73,58.16,64.68,71.08,77.49,90.43],
            'grupoC': [53.80,53.80,60.49,67.26,73.93,80.59,94.04],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [64.81,72.72,80.67,88.71,96.62,112.70],
            'grupoB': [72.01,80.80,89.63,98.57,107.36,125.22],
            'grupoC': [74.89,84.03,93.22,102.51,111.65,130.23],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [81.98,92.10,102.51,112.71,122.78,143.30],
            'grupoB': [91.09,102.33,113.90,125.24,136.42,159.22],
            'grupoC': [94.73,106.42,118.46,130.24,141.88,165.59],
        }),
    ],
    2: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [16.81,16.81,18.07,19.42,21.68,23.57,27.84,36.13,38.85,43.36,47.15,55.69],
            'grupoB': [18.68,18.68,20.07,21.57,24.09,26.19,30.94,40.15,43.16,48.17,52.39,61.88],
            'grupoC': [19.43,19.43,20.88,22.44,25.05,27.23,32.18,41.76,44.89,50.10,54.49,64.35],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [24.65,30.43,30.43,36.24,36.24,36.24,40.74,48.88,53.54,64.24,70.67],
            'grupoB': [27.39,33.81,33.81,40.27,40.27,40.27,45.26,54.32,59.48,71.38,78.52],
            'grupoC': [28.49,35.17,35.17,41.88,41.88,41.88,47.07,56.49,61.86,74.24,81.66],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [25.35,34.10,34.10,42.88,42.88,42.88,45.71,54.85,60.20],
            'grupoB': [28.17,37.89,37.89,47.64,47.64,47.64,50.79,60.95,66.89],
            'grupoC': [29.29,39.41,39.41,49.54,49.54,49.54,52.82,63.39,69.56],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [37.48,42.05,46.86,51.57,56.12,65.50,72.05,73.57,73.57],
            'grupoB': [41.65,46.73,52.06,57.30,62.36,72.78,80.05,81.75,81.75],
            'grupoC': [43.31,48.60,54.15,59.59,64.85,75.69,83.26,85.02,85.02],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [40.74,40.74,45.71,50.93,56.05,61.00,71.20],
            'grupoB': [45.26,45.26,50.79,56.59,62.27,67.78,79.11],
            'grupoC': [47.07,47.07,52.82,58.86,64.76,70.49,82.28],
        }),
        ([598], [598], {
            'crudo':  [71.20],
            'grupoB': [79.11],
            'grupoC': [82.28],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [40.74,40.74,45.71,50.93,56.05,61.00,71.20],
            'grupoB': [45.26,45.26,50.79,56.59,62.27,67.78,79.11],
            'grupoC': [47.07,47.07,52.82,58.86,64.76,70.49,82.28],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [53.54,53.54,60.20,66.94,73.57,80.20,93.59],
            'grupoB': [59.48,59.48,66.89,74.38,81.75,89.11,103.99],
            'grupoC': [61.86,61.86,69.56,77.35,85.02,92.68,108.15],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [53.54,53.54,60.20,66.94,73.57,80.20,93.59],
            'grupoB': [59.48,59.48,66.89,74.38,81.75,89.11,103.99],
            'grupoC': [61.86,61.86,69.56,77.35,85.02,92.68,108.15],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [74.53,83.63,92.77,102.02,111.12,129.60],
            'grupoB': [82.81,92.92,103.08,113.36,123.46,144.00],
            'grupoC': [86.13,96.64,107.20,117.89,128.40,149.76],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [94.27,105.91,117.89,129.62,141.19,164.79],
            'grupoB': [104.75,117.68,130.99,144.02,156.88,183.10],
            'grupoC': [108.94,122.38,136.23,149.78,163.16,190.43],
        }),
    ],
    3: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [28.96,28.96,29.66,30.48,31.24,33.18,35.57,38.98,42.62,44.76,47.35,56.82],
            'grupoB': [31.76,31.76,32.76,33.80,34.43,35.76,38.69,42.33,47.67,49.96,52.98,63.57],
            'grupoC': [33.04,33.04,34.07,35.16,35.80,37.19,40.24,44.02,49.58,51.95,55.10,66.11],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [44.07,45.59,47.19,48.38,50.04,51.28,53.66,58.51,63.45,70.50,84.61],
            'grupoB': [50.31,51.13,53.13,54.24,59.61,60.38,64.15,72.73,79.06,87.84,105.41],
            'grupoC': [52.32,53.18,55.26,56.41,62.00,62.80,66.72,75.64,82.22,91.35,109.63],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [45.16,46.31,47.62,48.94,50.55,51.71,54.83,59.46,65.95],
            'grupoB': [50.93,51.55,54.03,54.87,60.21,61.46,64.92,74.01,80.72],
            'grupoC': [52.97,53.61,56.20,57.07,62.62,63.92,67.52,76.97,83.95],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [45.82,46.97,48.97,49.46,50.69,52.45,56.63,60.68,67.51],
            'grupoB': [53.20,54.21,56.02,57.17,61.64,62.98,65.76,75.25,81.30],
            'grupoC': [55.33,56.38,58.26,59.45,64.10,65.49,68.39,78.26,84.55],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [47.59,47.59,48.77,51.10,52.37,54.74,59.92],
            'grupoB': [57.65,57.65,59.26,63.21,65.10,68.82,75.86],
            'grupoC': [59.96,59.96,61.63,65.73,67.70,71.58,78.89],
        }),
        ([598], [598], {
            'crudo':  [62.81],
            'grupoB': [79.06],
            'grupoC': [82.22],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [49.35,49.35,50.58,51.85,53.14,54.74,62.81],
            'grupoB': [59.26,59.26,63.21,64.92,66.59,69.74,79.06],
            'grupoC': [61.63,61.63,65.73,67.52,69.26,72.53,82.22],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [56.76,56.76,57.99,59.63,61.11,65.26,76.89],
            'grupoB': [68.47,68.47,69.94,73.66,74.54,78.82,94.81],
            'grupoC': [71.21,71.21,72.74,76.60,77.52,81.97,98.60],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [61.69,61.69,63.22,64.80,66.43,67.70,81.17],
            'grupoB': [74.60,74.60,75.71,80.55,81.48,85.46,105.33],
            'grupoC': [77.59,77.59,78.74,83.77,84.74,88.88,109.54],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [94.65,99.64,102.82,103.88,108.45,132.08],
            'grupoB': [111.59,117.27,123.11,125.55,133.47,159.51],
            'grupoC': [116.06,121.96,128.04,130.57,138.81,165.89],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [118.32,124.55,127.65,130.85,136.61,161.28],
            'grupoB': [142.67,146.56,154.69,156.92,168.25,200.69],
            'grupoC': [148.38,152.42,160.88,163.20,174.98,208.72],
        }),
    ],
    4: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [26.67,26.67,27.20,28.08,28.75,30.41,32.66,37.98,39.04,41.00,45.86,52.08],
            'grupoB': [29.62,29.66,29.89,30.50,31.26,33.41,36.23,41.53,44.73,46.36,52.55,59.63],
            'grupoC': [30.80,30.84,31.08,31.71,32.52,34.75,37.68,43.19,46.52,48.22,54.65,62.01],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [45.24,47.50,48.97,49.74,50.73,51.55,54.60,62.46,68.61,76.24,91.47],
            'grupoB': [51.67,53.86,55.72,57.41,61.26,61.67,65.61,76.85,84.34,93.74,112.47],
            'grupoC': [53.74,56.01,57.95,59.71,63.71,64.13,68.23,79.92,87.71,97.49,116.97],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [45.86,48.59,50.15,50.87,51.86,52.78,55.64,63.25,69.86],
            'grupoB': [52.45,54.47,56.45,58.25,62.60,63.54,66.53,78.24,85.69],
            'grupoC': [54.55,56.65,58.71,60.58,65.10,66.08,69.19,81.37,89.12],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [46.44,49.12,50.69,51.14,52.71,54.20,56.78,64.42,70.42],
            'grupoB': [53.89,55.41,57.75,59.30,65.41,66.68,68.22,79.22,86.45],
            'grupoC': [56.04,57.63,60.06,61.67,68.02,69.34,70.94,82.39,89.91],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [49.20,49.20,50.66,53.66,54.64,55.64,60.71],
            'grupoB': [59.53,59.53,61.67,65.61,67.43,70.05,77.20],
            'grupoC': [61.91,61.91,64.13,68.23,70.13,72.85,80.28],
        }),
        ([598], [598], {
            'crudo':  [63.42],
            'grupoB': [78.79],
            'grupoC': [81.94],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [50.15,50.15,51.14,54.44,55.95,57.20,63.42],
            'grupoB': [59.96,59.96,63.02,66.73,68.66,70.94,78.79],
            'grupoC': [62.36,62.36,65.54,69.40,71.41,73.78,81.94],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [59.91,59.91,61.50,65.95,67.18,68.74,73.96],
            'grupoB': [70.46,70.46,72.93,79.22,80.72,82.79,93.46],
            'grupoC': [73.28,73.28,75.85,82.39,83.95,86.10,97.20],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [64.56,64.56,66.53,68.61,70.21,72.25,79.41],
            'grupoB': [77.72,77.72,79.45,84.34,87.56,90.90,100.29],
            'grupoC': [80.83,80.83,82.63,87.71,91.06,94.54,104.30],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [89.53,91.70,96.98,100.29,104.15,115.84],
            'grupoB': [108.89,112.63,120.22,124.05,129.26,142.22],
            'grupoC': [113.25,117.14,125.03,129.01,134.43,147.91],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [112.73,115.48,123.18,127.56,130.91,141.40],
            'grupoB': [136.13,139.89,151.21,153.54,164.99,179.14],
            'grupoC': [141.58,145.48,157.25,159.68,171.59,186.30],
        }),
    ],
    5: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [22.67,22.67,23.12,23.87,24.44,25.85,27.76,32.28,33.19,34.85,38.98,44.27],
            'grupoB': [25.17,25.21,25.40,25.92,26.58,28.40,30.80,35.30,38.02,39.41,44.67,50.68],
            'grupoC': [26.18,26.22,26.42,26.96,27.64,29.54,32.03,36.71,39.54,40.99,46.45,52.71],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [38.46,40.37,41.62,42.28,43.12,43.82,46.41,53.09,58.32,64.80,77.75],
            'grupoB': [43.92,45.78,47.36,48.80,52.07,52.42,55.77,65.32,71.69,79.68,95.60],
            'grupoC': [45.68,47.61,49.26,50.75,54.15,54.51,58.00,67.93,74.56,82.87,99.43],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [38.98,41.30,42.62,43.24,44.08,44.86,47.30,53.76,59.38],
            'grupoB': [44.59,46.30,47.98,49.51,53.21,54.01,56.55,66.50,72.84],
            'grupoC': [46.37,48.15,49.90,51.49,55.34,56.17,58.81,69.16,75.75],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [39.48,41.75,43.08,43.47,44.80,46.07,48.26,54.76,59.85],
            'grupoB': [45.80,47.10,49.09,50.41,55.60,56.67,57.98,67.34,73.48],
            'grupoC': [47.64,48.98,51.05,52.42,57.82,58.94,60.30,70.03,76.42],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [41.82,41.82,43.06,45.61,46.45,47.30,51.60],
            'grupoB': [50.60,50.60,52.42,55.77,57.32,59.54,65.62],
            'grupoC': [52.63,52.63,54.51,58.00,59.61,61.93,68.24],
        }),
        ([598], [598], {
            'crudo':  [53.91],
            'grupoB': [66.97],
            'grupoC': [69.65],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [42.62,42.62,43.47,46.27,47.56,48.62,53.91],
            'grupoB': [50.97,50.97,53.56,56.72,58.36,60.30,66.97],
            'grupoC': [53.01,53.01,55.71,58.99,60.70,62.71,69.65],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [50.92,50.92,52.28,56.05,57.10,58.43,62.86],
            'grupoB': [59.89,59.89,61.99,67.34,68.61,70.37,79.44],
            'grupoC': [62.28,62.28,64.47,70.03,71.36,73.18,82.62],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [54.87,54.87,56.55,58.32,59.68,61.42,67.50],
            'grupoB': [66.06,66.06,67.53,71.69,74.42,77.27,85.25],
            'grupoC': [68.71,68.71,70.24,74.56,77.40,80.36,88.66],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [76.10,77.95,82.43,85.25,88.53,98.46],
            'grupoB': [92.56,95.74,102.19,105.44,109.87,120.89],
            'grupoC': [96.26,99.57,106.28,109.66,114.27,125.73],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [95.82,98.16,104.71,108.42,111.27,120.19],
            'grupoB': [115.71,118.91,128.53,130.51,140.25,152.26],
            'grupoC': [120.34,123.66,133.67,135.73,145.86,158.36],
        }),
    ],
    6: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [27.75,27.75,28.50,29.24,29.95,31.91,34.57,40.15,41.95,44.46,48.17,52.89],
            'grupoB': [30.77,30.77,31.52,32.29,33.52,34.82,37.98,43.55,47.34,49.52,55.60,63.10],
            'grupoC': [32.00,32.00,32.78,33.58,34.86,36.21,39.50,45.30,49.23,51.51,57.83,65.62],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [48.55,49.75,51.78,53.06,54.25,55.22,57.63,67.61,74.27,82.52,99.02],
            'grupoB': [54.67,56.02,58.15,59.59,65.23,66.85,69.58,81.50,89.47,99.41,119.28],
            'grupoC': [56.86,58.26,60.48,61.97,67.84,69.53,72.36,84.77,93.05,103.39,124.05],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [48.93,50.52,52.66,54.17,55.01,55.83,59.28,68.74,76.29],
            'grupoB': [56.24,57.64,59.09,60.56,65.23,66.82,71.94,81.50,89.47],
            'grupoC': [58.49,59.95,61.45,62.98,67.84,69.50,74.82,84.77,93.05],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [51.01,52.27,53.56,54.90,56.28,57.68,60.00,70.19,77.83],
            'grupoB': [58.22,59.65,61.15,62.68,66.99,68.65,73.35,83.53,91.82],
            'grupoC': [60.55,62.04,63.60,65.19,69.67,71.39,76.28,86.87,95.50],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [53.13,53.13,54.44,57.63,59.06,60.53,67.86],
            'grupoB': [63.10,63.10,64.66,69.58,71.32,73.09,74.91],
            'grupoC': [65.62,65.62,67.25,72.36,74.17,76.01,77.91],
        }),
        ([598], [598], {
            'crudo':  [68.57],
            'grupoB': [82.40],
            'grupoC': [85.69],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [54.24,54.24,55.41,58.25,60.06,62.03,68.57],
            'grupoB': [63.77,63.77,65.45,70.44,72.00,73.93,82.40],
            'grupoC': [66.32,66.32,68.06,73.26,74.88,76.89,85.69],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [63.07,63.07,64.62,67.61,70.98,74.54,80.18],
            'grupoB': [74.67,74.67,76.53,81.50,85.52,89.84,99.71],
            'grupoC': [77.66,77.66,79.60,84.77,88.94,93.43,103.70],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [69.69,69.69,71.42,74.27,75.49,77.49,86.22],
            'grupoB': [82.36,82.36,84.41,89.47,90.20,94.62,106.45],
            'grupoC': [85.65,85.65,87.78,93.05,93.81,98.40,110.71],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [94.46,96.87,103.07,105.41,111.41,120.68],
            'grupoB': [112.66,115.57,124.64,127.86,137.54,150.52],
            'grupoC': [117.17,120.19,129.63,132.97,143.04,156.54],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [118.08,121.10,131.79,135.07,139.24,150.85],
            'grupoB': [140.86,144.45,159.82,165.25,171.94,188.14],
            'grupoC': [146.50,150.23,166.22,171.86,178.81,195.67],
        }),
    ],
    7: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [16.72,16.72,17.97,19.31,21.56,23.44,27.69,35.94,38.64,43.12,46.90,55.39],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'crudo':  [24.52,30.27,30.27,36.05,36.05,36.05,40.52,48.62,53.25,63.90,70.29],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [25.21,33.92,33.92,42.64,42.64,42.64,45.46,54.56,59.87],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'crudo':  [37.28,41.83,46.60,51.29,55.82,65.14,71.66,73.17,73.17],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [40.52,40.52,45.46,50.66,55.74,60.68,70.82],
        }),
        ([598], [598], {
            'crudo':  [70.82],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [40.52,40.52,45.46,50.66,55.74,60.68,70.82],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [53.25,53.25,59.87,66.58,73.17,79.77,93.09],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'crudo':  [53.25,53.25,59.87,66.58,73.17,79.77,93.09],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'crudo':  [74.13,83.18,92.27,101.47,110.52,128.90],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'crudo':  [93.76,105.34,117.25,128.92,140.43,163.90],
        }),
    ],
}

# ── COMPLEMENTOS (pág. 35) y COSTADOS (pág. 36) ────────────────────────────
#
# Los complementos van por PIEZA, con las mismas tres columnas. Los costados
# van por SUPERFICIE en cm² y tienen DOS tablas, porque la chapa cambia el
# precio de partida y no solo con un porcentaje: una para ROBLE-FRESNO y otra
# para ROBLE NUDOS Y NOGAL. Aplicar el +10/+15 % sobre la primera daría otro
# número — la tarifa ya trae la segunda hecha.
COMPLEMENTOS = [
    ('CORNISA', [32.08, 38.23, 42.46]),
    ('CORNISA DISEÑO', [69.65, 75.63, 79.77]),
    ('PORTALUZ', [28.96, 34.69, 38.55]),
    ('PORTALUZ DISEÑO', [61.54, 67.08, 70.82]),
    ('REGLETA DISEÑO 70 - DISEÑO Nº 3', [37.45, 45.87, 47.78]),
    ('REGLETA DISEÑO 90 - DISEÑO Nº 3', [48.16, 58.93, 61.45]),
    ('REGLETA DISEÑO 194 - DISEÑO Nº 3', [78.65, 96.27, 100.34]),
    ('PANEL 2440X600X4 MM', [40.48, 52.31, 58.08]),
    ('TERMINAL ALTO 700X300X300', [76.08, 87.16, 96.84]),
    ('TERMINAL ALTO 900X300X300', [88.28, 101.11, 112.34]),
    ('TERMINAL BAJO 700X300X600', [86.21, 98.77, 109.75]),
    ('TERMINAL COLUMNA 1940X300X600', [256.66, 294.02, 326.69]),
    ('DECORATIVO/BOTELLERO 700X300X300', [68.97, 79.03, 87.8]),
    ('DECORATIVO/BOTELLERO 900X300X300', [82.17, 94.14, 104.59]),
    ('PLATERO 900X800 (TIPO 1-TIPO 2-TIPO 3)', [480.95, 562.51, 646.89]),
    ('PLATERO 700X800 (TIPO 1-TIPO 2-TIPO 3)', [399.57, 467.32, 529.54]),
    ('CAMPANA PIRAMIDE', [327.16, 376.24, 427.03]),
    ('CAMPANA TRAPECIO', [352.5, 405.87, 461.08]),
    ('CAMPANA RINCON', [351.25, 407.61, 465.9]),
    ('CAMPANA 5 CARAS', [351.25, 407.61, 465.9]),
    ('CAMPANA DISEÑO A', [770.95, 853.22, 894.11]),
    ('CAMPANA DISEÑO B', [545.27, 623.16, 664.06]),
    ('CAMPANA DISEÑO C', [545.27, 623.16, 664.06]),
    ('CAMPANA DISEÑO D', [545.27, 623.16, 664.06]),
    ('CAMPANA DISEÑO E', [629.01, 712.74, 753.64]),
    ('CAMPANA DISEÑO F', [734.24, 814.44, 854.1]),
    ('CAMPANA DISEÑO Nº 1', [629.01, 712.74, 753.64]),
    ('CAMPANA DISEÑO Nº 4', [545.27, 623.16, 664.06]),
    ('CAMPANA DISEÑO Nº 6', [545.27, 623.16, 664.06]),
    ('CAMPANA DISEÑO Nº 9', [627.06, 716.63, 763.67]),
]

COSTADOS_ROBLE_FRESNO = [
    ('HASTA 2000', [20.82, 24.5, 26.93, 119.63]),
    ('HASTA 2500', [25.99, 30.58, 33.98, 129.08]),
    ('HASTA 3000', [32.93, 38.74, 40.79, 149.1]),
    ('HASTA 3500', [36.38, 42.8, 47.58, 179.05]),
    ('HASTA 4000', [41.59, 48.93, 54.39, 193.96]),
    ('HASTA 4500', [46.8, 55.06, 61.16, 213.79]),
    ('HASTA 5000', [51.99, 61.16, 67.97, 238.57]),
    ('HASTA 5500', [57.18, 67.27, 74.8, 253.48]),
    ('HASTA 6000', [62.39, 73.4, 81.56, 272.96]),
    ('HASTA 6500', [67.6, 79.53, 88.36, 289.38]),
    ('HASTA 7000', [72.85, 85.71, 95.14, 305.77]),
    ('HASTA 7500', [77.98, 91.74, 101.93, 320.7]),
    ('HASTA 8000', [83.19, 97.87, 108.73, 343.29]),
    ('HASTA 8500', [88.38, 103.98, 115.52, 347.36]),
    ('HASTA 9000', [93.57, 110.09, 122.35, 382.63]),
    ('HASTA 9500', [97.43, 114.63, 133.58, 376.99]),
    ('HASTA 10000', [103.98, 122.32, 135.92, 391.09]),
    ('HASTA 10500', [109.17, 128.43, 142.72, 399.57]),
    ('DE 11000 A 14640', [114.4, 134.58, 149.52, 435.53]),
]

COSTADOS_NUDOS_NOGAL = [
    ('HASTA 2000', [23.95, 28.17, 30.97, 119.63]),
    ('HASTA 2500', [29.89, 35.17, 39.07, 129.08]),
    ('HASTA 3000', [37.87, 44.55, 46.91, 149.1]),
    ('HASTA 3500', [41.83, 49.21, 54.72, 179.05]),
    ('HASTA 4000', [47.82, 56.26, 62.55, 193.96]),
    ('HASTA 4500', [53.82, 63.31, 70.34, 213.79]),
    ('HASTA 5000', [59.79, 70.34, 78.16, 238.57]),
    ('HASTA 5500', [65.76, 77.36, 86.02, 253.48]),
    ('HASTA 6000', [71.75, 84.41, 93.79, 272.96]),
    ('HASTA 6500', [77.74, 91.46, 101.62, 289.38]),
    ('HASTA 7000', [83.78, 98.56, 109.41, 305.77]),
    ('HASTA 7500', [89.68, 105.5, 117.22, 320.7]),
    ('HASTA 8000', [95.67, 112.55, 125.04, 343.29]),
    ('HASTA 8500', [101.64, 119.58, 132.85, 347.36]),
    ('HASTA 9000', [107.61, 126.6, 140.71, 382.63]),
    ('HASTA 9500', [112.05, 131.82, 153.62, 376.99]),
    ('HASTA 10000', [119.57, 140.67, 156.3, 391.09]),
    ('HASTA 10500', [125.54, 147.7, 164.13, 399.57]),
    ('DE 11000 A 14640', [131.56, 154.77, 171.95, 435.53]),
]

# ── LAS REGLAS DE LA PÁGINA 18 ─────────────────────────────────────────────
#
# Están escritas ahí y en ningún otro sitio, así que si no viajan con la
# tarifa no las aplica nadie. Y son dinero: una vitrina mal tarifada se cobra
# un 20 % o un 50 % por debajo.
#
# Las VITRINAS de once modelos concretos van un +20 % sobre el valor de la
# puerta. La lista es CERRADA: en los demás modelos la vitrina no lleva ese
# recargo, así que ampliarla «por si acaso» cobraría de más.
VITRINA_MAS_20 = ["MADRID", "VEGA", "PALMA", "SALZBURGO", "TRÍPOLI", "LAREDO",
                  "HANOI", "PALENCIA", "BARBADOS", "NUBE", "CADAQUÉS"]
VITRINA_PCT = 20            # sobre el valor de la puerta, esos once modelos
VITRINA_PALILLERIA_PCT = 50  # palillería y celosía, en cualquier modelo

PIGMENTADO_FUERA_DE_CARTA_PCT = 25  # sobre GRUPO C
TINTE_FUERA_DE_CARTA_PCT = 25       # sobre GRUPO B
VETA_CONSECUTIVA_PCT = 25
XOLID_PCT = 15

# Acabados especiales de la pág. 20, sobre su propio grupo.
TINTE_PATINA_PCT = 10        # GRUPO B + 10 %
PIGMENTO_PATINA_PCT = 10     # GRUPO C + 10 %
PORO_ARENADO_PCT = 10

# El grupo 7 (abeto tricapa) no tiene columnas B y C: sus acabados son
# recargos sobre el crudo (pág. 33).
ACABADOS_ABETO = [
    ("pigmento",    "Pigmento",     20),
    ("poroArenado", "Poro arenado", 10),
    ("tinte",       "Tinte",        10),
]

# ── ANOMALÍAS DE LA TARIFA, COMPROBADAS CONTRA EL PDF ──────────────────────
#
# El ATAMBORADO baja de 382,63 € a 376,99 € al pasar de «HASTA 9000» a «HASTA
# 9500»: una pieza más grande por menos dinero. Comprobado a 400 dpi en la
# pág. 36 — es la tarifa de ACB, no la transcripción. Se copia lo que el
# proveedor factura, no lo que debería.
#
# En esa misma fila, la columna de GRUPO C da un salto raro (122,35 → 133,58 →
# 135,92 €, cuando el paso normal ronda los 7 €). No rompe el orden, así que no
# salta solo; queda anotado porque lo más probable es que sea el mismo dedazo.
#
# LISTA CERRADA a propósito: una inversión nueva se pone roja, que es el fallo
# que se busca. Aflojar la tolerancia hasta que dejen de saltar taparía erratas
# futuras con la excusa de esta.
INVERSIONES_DE_LA_TARIFA = {("atamborado", "HASTA 9500")}

COSTADO_30MM_PCT = 25  # pág. 36
# «COSTADOS A DOS CARAS 22 mm ABETO TRICAPA: se cobran como puerta lisa»
COSTADO_ABETO = "se cobra como puerta lisa"
# Y la regla de la medida que no está, la misma que en la laca.
MEDIDA_ESPECIAL = "sube a la medida inmediata superior"


# ── VALIDACIÓN ─────────────────────────────────────────────────────────────
TOL = 0.011
fallos = []
IDS_CHAPA = {c for c, _, _ in CHAPAS}

# 1. La rejilla es la misma en los siete grupos.
forma = [(a, w) for a, w, _ in MATRICES[1]]
for g in range(2, 8):
    if [(a, w) for a, w, _ in MATRICES[g]] != forma:
        fallos.append(f"el grupo {g} no tiene la misma rejilla que el grupo 1")

for g, bloques in MATRICES.items():
    for altos, anchos, precios in bloques:
        for aid, vals in precios.items():
            if len(vals) != len(anchos):
                fallos.append(f"G{g} {altos} {aid}: {len(vals)} precios para "
                              f"{len(anchos)} anchos")
                continue
            # 2. Dentro de un alto, el precio sube con el ancho.
            for (w1, v1), (w2, v2) in zip(zip(anchos, vals),
                                          list(zip(anchos, vals))[1:]):
                if v1 - v2 > TOL:
                    fallos.append(f"G{g} alto {altos} {aid}: {w2} ({v2}) "
                                  f"cuesta menos que {w1} ({v1})")
            for w, v in zip(anchos, vals):
                if not (1 <= v <= 400):
                    fallos.append(f"G{g} {altos}x{w} {aid} a {v} €")
        # 3. Crudo ≤ grupo B ≤ grupo C, siempre. Es lo que hace que la columna
        #    signifique algo; si se cruzaran, sería que están desplazadas.
        if "grupoB" in precios:
            for i, w in enumerate(anchos):
                c, b, cc = (precios["crudo"][i], precios["grupoB"][i],
                            precios["grupoC"][i])
                if not (c - TOL <= b and b - TOL <= cc):
                    fallos.append(f"G{g} {altos}x{w}: crudo/B/C no suben "
                                  f"({c}, {b}, {cc})")

# 4. El grupo 7 va SOLO en crudo, y los demás llevan las tres columnas.
for g, bloques in MATRICES.items():
    esperadas = {"crudo"} if g == 7 else {"crudo", "grupoB", "grupoC"}
    for altos, _, precios in bloques:
        if set(precios) != esperadas:
            fallos.append(f"G{g} {altos} tiene las columnas {sorted(precios)} "
                          f"y toca {sorted(esperadas)}")

# 5. Los modelos: grupo que existe, chapas que existen, recargo razonable.
vistos = set()
for nombre, lineas, antiguo in MODELOS:
    if nombre in vistos:
        fallos.append(f"{nombre} sale dos veces")
    vistos.add(nombre)
    if not lineas:
        fallos.append(f"{nombre} no dice en qué grupo está")
    todas = [c for chapas, _, _ in lineas for c in chapas]
    if len(todas) != len(set(todas)):
        fallos.append(f"{nombre} repite una chapa en dos líneas: {todas}")
    for chapas, grupo, recargo in lineas:
        if grupo not in MATRICES:
            fallos.append(f"{nombre} dice grupo {grupo}, que no existe")
        if not (0 <= recargo <= 30):
            fallos.append(f"{nombre} lleva un {recargo}% de recargo")
        for c in chapas:
            if c not in IDS_CHAPA:
                fallos.append(f"{nombre} pide la chapa «{c}», que no existe")
        if not antiguo and not chapas:
            fallos.append(f"{nombre} es un modelo actual y no dice en qué "
                          f"chapas se fabrica")
        # El grupo 7 es el abeto tricapa: pedirlo en otra chapa, o el abeto en
        # otro grupo, sería tarifar una madera al precio de otra.
        if grupo == 7 and chapas and chapas != ["abeto"]:
            fallos.append(f"{nombre}: el grupo 7 es abeto tricapa y aquí pide "
                          f"{chapas}")
        if "abeto" in chapas and grupo != 7:
            fallos.append(f"{nombre}: el abeto tricapa va en el grupo 7 y aquí "
                          f"pide el {grupo}")

# 6. Los once de la vitrina tienen que existir como modelo.
for v in VITRINA_MAS_20:
    if v not in vistos:
        fallos.append(f"la lista de vitrinas nombra «{v}», que no es un modelo")

# 7. Complementos y costados: nada gratis, y el costado sube con la superficie.
for nombre, vals in COMPLEMENTOS:
    if len(vals) != 3:
        fallos.append(f"complemento {nombre}: {len(vals)} precios, tocan 3")
    if not (vals[0] - TOL <= vals[1] and vals[1] - TOL <= vals[2]):
        fallos.append(f"complemento {nombre}: crudo/B/C no suben ({vals})")
    for v in vals:
        if not (1 <= v <= 1000):
            fallos.append(f"complemento {nombre} a {v} €, fuera de rango")
for etiqueta, tabla in (("roble-fresno", COSTADOS_ROBLE_FRESNO),
                        ("nudos-nogal", COSTADOS_NUDOS_NOGAL)):
    if len(tabla) != 19:
        fallos.append(f"costados {etiqueta}: {len(tabla)} tramos, tocan 19")
    for k, col in enumerate(("crudo", "grupoB", "grupoC", "atamborado")):
        for (n1, v1), (n2, v2) in zip(tabla, tabla[1:]):
            if (col, n2) in INVERSIONES_DE_LA_TARIFA:
                continue
            if v1[k] - v2[k] > TOL:
                fallos.append(f"costados {etiqueta} col {k}: «{n2}» ({v2[k]}) "
                              f"cuesta menos que «{n1}» ({v1[k]})")
# Y el de nudos/nogal cuesta MÁS que el de roble-fresno: es la madera cara.
for (n1, v1), (n2, v2) in zip(COSTADOS_ROBLE_FRESNO, COSTADOS_NUDOS_NOGAL):
    for k in range(3):
        if v1[k] - v2[k] > TOL:
            fallos.append(f"costado «{n1}» col {k}: el de nudos/nogal ({v2[k]}) "
                          f"cuesta menos que el de roble/fresno ({v1[k]})")

if fallos:
    print("REVISAR la transcripción de la madera:")
    for f in fallos:
        print("  ", f)
    raise SystemExit(1)

n = sum(len(v) for bs in MATRICES.values() for _, _, p in bs for v in p.values())
actuales = sum(1 for _, _, a in MODELOS if not a)
print("✓ validado: rejilla igual en los siete grupos, el precio sube con el "
      "ancho, crudo ≤ grupo B ≤ grupo C y cada chapa cae en su grupo")
print(f"  modelos: {actuales} actuales + {len(MODELOS)-actuales} antiguos · "
      f"precios de matriz: {n} · complementos: {len(COMPLEMENTOS)}")


# ── EMITIR EL FICHERO ──────────────────────────────────────────────────────
def js(o):
    return json.dumps(o, ensure_ascii=False)


def ident(nombre):
    """El id con el que viaja un modelo. Se deriva del nombre para no mantener
    dos listas; los espacios y los acentos no valen en una clave."""
    tabla = str.maketrans("ÁÉÍÓÚÜÑ", "AEIOUUN")
    return nombre.translate(tabla).replace(" ", "_").replace("-", "_")


out = ['''/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// TARIFA DE MADERA DEL GRUPO ACB, 2026 — páginas 17 a 36.
//
// Se genera con `herramientas/tarifa_acb_madera.py`, que VALIDA los números
// antes de escribir nada. Es la tercera colección de ACB PUERTAS: el canteado
// está en `acbPuertas.js` y la laca en `acbLaca.js`.
//
// LA MADERA TIENE UNA VUELTA MÁS QUE LA LACA. Allí el GRUESO decidía el grupo;
// aquí lo decide la CHAPA:
//
//     precio = matriz(GRUPO, acabado, alto, ancho)
//              × (1 + recargo del modelo)
//              × (1 + recargo de la chapa)
//
// Un MADRID en fresno es GRUPO 1 y en abeto tricapa es GRUPO 7 — otra matriz
// entera, no un porcentaje. Y la chapa lleva además su propio recargo: NOGAL
// +10 %, ROBLE NUDOS +15 %, en TODOS los grupos.
//
// PRECIOS DE TARIFA, ANTES DE DESCUENTO. El de ACB lo teclea el master.''']

out.append("""
/** Las chapas y lo que cuestan (pág. 18 y el pie de las catorce páginas de
 *  matriz). El recargo es de la CHAPA, no del modelo: va en todos los grupos. */
export const ACB_MADERA_CHAPAS = %s;

/** Las que se le ofrecen a un modelo ANTIGUO, que la tarifa lista sin sus
 *  chapas. Son las cuatro que llevan todos los modelos actuales y cuyo recargo
 *  está escrito para cualquier modelo. Fuera quedan el ALDER (lo lleva un solo
 *  modelo) y el ABETO TRICAPA, que no es una chapa más sino el GRUPO 7 entero. */
export const ACB_MADERA_CHAPAS_DE_UN_ANTIGUO = ["fresno", "roble", "nogal", "robleNudos"];

/** Las tres columnas de precio de cada matriz. El GRUPO 7 (abeto tricapa) solo
 *  tiene la de crudo: sus acabados son recargos sobre ella. */
export const ACB_MADERA_ACABADOS = %s;

/** Los acabados del abeto tricapa (pág. 33), que son recargos y no columnas. */
export const ACB_MADERA_ACABADOS_ABETO = %s;

/** La carta de acabados (pág. 20): qué códigos entran en cada grupo. Es lo que
 *  dice si el acabado que pide el cliente se cobra por la columna B o por la C.
 *  OJO: en roble nudos la tarifa salta del H03 al H05 — el H04 no existe, y no
 *  se rellena. */
export const ACB_MADERA_CARTA = %s;""" % (
    js([{"id": c, "label": l, "recargo": r} for c, l, r in CHAPAS]),
    js([{"id": a, "label": l} for a, l in ACABADOS]),
    js([{"id": a, "label": l, "recargo": r} for a, l, r in ACABADOS_ABETO]),
    js(ACABADOS_CARTA)))

out.append("""
/** LOS MODELOS (págs. 19 y 19 bis).
 *
 *  `lineas` es una por juego de chapas, porque LA CHAPA PUEDE CAMBIAR EL
 *  GRUPO y no solo el recargo: MADRID en abeto tricapa es GRUPO 7 y en
 *  fresno/nogal/roble es GRUPO 1 — dos matrices distintas. Igual PALENCIA,
 *  PALMA y VEGA.
 *
 *  `antiguo` marca los que la tarifa lista aparte. Siguen pidiéndose, pero el
 *  PDF NO dice en qué chapas se fabrican: por eso su lista va vacía en vez de
 *  copiada de otro modelo parecido. */
export const ACB_MADERA_MODELOS = [""")
for nombre, lineas, antiguo in MODELOS:
    out.append("  { id: %s, nombre: %s, antiguo: %s, lineas: %s }," % (
        js(ident(nombre)), js(nombre), js(antiguo),
        js([{"chapas": ch, "grupo": g, "recargo": r} for ch, g, r in lineas])))
out.append("];\n")

out.append("""/** LAS SIETE MATRICES DE GRUPO (págs. 21 a 34), en MILÍMETROS.
 *  Un alto como «1198 & 1298» son DOS medidas al mismo precio. La madera NO
 *  lleva el bloque de 418 que sí tienen el canteado y la laca. */
export const ACB_MADERA_MATRICES = {""")
for g in sorted(MATRICES):
    out.append("  %d: [" % g)
    for altos, anchos, precios in MATRICES[g]:
        out.append("    { altos: %s, anchos: %s, precios: %s }," % (
            js(altos), js(anchos), js(precios)))
    out.append("  ],")
out.append("};\n")

out.append("""/** COMPLEMENTOS por pieza (pág. 35), en el orden de ACB_MADERA_ACABADOS. */
export const ACB_MADERA_COMPLEMENTOS = %s;

/** COSTADOS (pág. 36), por superficie en cm². SON DOS TABLAS y no una con un
 *  porcentaje: la tarifa trae hecha la de roble nudos y nogal, así que
 *  aplicarle el +10/+15 %% a la primera daría otro número. Columnas: crudo,
 *  grupo B, grupo C y atamborado. */
export const ACB_MADERA_COSTADOS = %s;
export const ACB_MADERA_COSTADOS_ACABADOS = %s;""" % (
    js([{"nombre": n, "precios": v} for n, v in COMPLEMENTOS]),
    js({"robleFresno": [{"hasta": n, "precios": v} for n, v in COSTADOS_ROBLE_FRESNO],
        "nudosNogal": [{"hasta": n, "precios": v} for n, v in COSTADOS_NUDOS_NOGAL]}),
    js(["crudo", "grupoB", "grupoC", "atamborado"])))

out.append("""
/** LAS REGLAS DE LA PÁGINA 18. Están escritas ahí y en ningún otro sitio: si
 *  no viajan con la tarifa no las aplica nadie, y son dinero — una vitrina mal
 *  tarifada se cobra un 20 %% o un 50 %% por debajo. */
export const ACB_MADERA_VITRINA_MAS_20 = %s;
export const ACB_MADERA_VITRINA_PCT = %s;
export const ACB_MADERA_VITRINA_PALILLERIA_PCT = %s;
export const ACB_MADERA_PIGMENTADO_FUERA_DE_CARTA_PCT = %s;
export const ACB_MADERA_TINTE_FUERA_DE_CARTA_PCT = %s;
export const ACB_MADERA_VETA_CONSECUTIVA_PCT = %s;
export const ACB_MADERA_XOLID_PCT = %s;
export const ACB_MADERA_TINTE_PATINA_PCT = %s;
export const ACB_MADERA_PIGMENTO_PATINA_PCT = %s;
export const ACB_MADERA_PORO_ARENADO_PCT = %s;
export const ACB_MADERA_COSTADO_30MM_PCT = %s;
export const ACB_MADERA_COSTADO_ABETO = %s;

/** «El precio para medidas especiales será igual al precio de la medida
 *  inmediata superior». NO SE INTERPOLA nunca. */
export const ACB_MADERA_MEDIDA_ESPECIAL = %s;""" % (
    js(VITRINA_MAS_20), VITRINA_PCT, VITRINA_PALILLERIA_PCT,
    PIGMENTADO_FUERA_DE_CARTA_PCT, TINTE_FUERA_DE_CARTA_PCT,
    VETA_CONSECUTIVA_PCT, XOLID_PCT, TINTE_PATINA_PCT, PIGMENTO_PATINA_PCT,
    PORO_ARENADO_PCT, COSTADO_30MM_PCT, js(COSTADO_ABETO),
    js(MEDIDA_ESPECIAL)))

out.append('''
/** Las chapas en las que ACB fabrica ese modelo. Lista vacía si el modelo no
 *  existe — o si es de los ANTIGUOS, que la tarifa lista sin sus chapas. */
export const chapasDeModeloACBMadera = (modelo) => {
  const m = ACB_MADERA_MODELOS.find((x) => x.id === modelo || x.nombre === modelo);
  if (!m) return [];
  const ids = m.lineas.flatMap((l) => l.chapas);
  /* Un ANTIGUO no trae lista en la tarifa, así que se ofrecen LAS CUATRO
     CORRIENTES y nada más. No es una lista a ojo: son las que aparecen en
     todos los modelos actuales y cuyo recargo está escrito en la pág. 18 para
     cualquier modelo. Las otras dos son de modelo concreto y quedan fuera a
     propósito — el ALDER solo lo lleva el CALABRIA MARCO MACIZO, y el ABETO
     TRICAPA no es una chapa más: es el GRUPO 7 entero, otra matriz, así que
     darlo por bueno aquí tarifaría por la tabla que no es. */
  if (!ids.length) return ACB_MADERA_CHAPAS.filter(
    (c) => ACB_MADERA_CHAPAS_DE_UN_ANTIGUO.includes(c.id));
  return ACB_MADERA_CHAPAS.filter((c) => ids.includes(c.id));
};

/** El grupo y el recargo de un modelo EN UNA CHAPA CONCRETA.
 *
 *  Devuelve `null` cuando ACB no lo fabrica en esa chapa. Coger la primera
 *  línea que hubiera tarifaría un MADRID de abeto (GRUPO 7) al precio del de
 *  fresno (GRUPO 1) — que no es un porcentaje de diferencia, es otra matriz. */
export const lineaDeModeloACBMadera = (modelo, chapa) => {
  const m = ACB_MADERA_MODELOS.find((x) => x.id === modelo || x.nombre === modelo);
  if (!m) return null;
  const l = m.lineas.find((x) => x.chapas.includes(chapa));
  if (l) return l;
  /* LOS ANTIGUOS SE TARIFAN IGUAL, PERO SE AVISA. La tarifa les da su GRUPO y
     el recargo de la chapa es de la pág. 18, universal — o sea que el precio
     se sabe. Lo que el PDF NO dice es en qué chapas los fabrica ACB.
     Devolverlos como `null` dejaría sin presupuestar unos modelos que están en
     tarifa; devolverlos callando haría creer que la combinación está
     confirmada. Se devuelven con `chapaSinConfirmar`, para que la pantalla lo
     diga y se pregunte al proveedor antes de cursar. */
  if (m.antiguo && m.lineas.length === 1 && m.lineas[0].chapas.length === 0
      && ACB_MADERA_CHAPAS_DE_UN_ANTIGUO.includes(chapa)) {
    return { ...m.lineas[0], chapaSinConfirmar: true };
  }
  return null;
};

/** El precio de tarifa del grupo, sin recargos. `null` si ACB no fabrica esa
 *  medida — que es distinto de que valga cero (CLAUDE.md, regla 7). */
export const precioBaseMaderaACB = (grupo, acabado, alto, ancho) => {
  const bloques = ACB_MADERA_MATRICES[Number(grupo)];
  if (!bloques) return null;
  const a = Number(alto), w = Number(ancho);
  const b = bloques.find((x) => x.altos.includes(a));
  if (!b) return null;
  const i = b.anchos.indexOf(w);
  if (i < 0) return null;
  const col = b.precios[acabado];
  return col && col[i] != null ? col[i] : null;
};

/** EL PRECIO DE UN FRENTE DE MADERA, con todo lo que lleva encima.
 *
 *  Devuelve `null` en cuanto falta un dato — modelo que no existe, chapa que
 *  no se fabrica, medida que no está en la matriz, o un acabado B/C pedido en
 *  el grupo 7, que solo tiene crudo. Nunca un número aproximado: un precio
 *  inventado no da ningún error, sale en el presupuesto.
 *
 *  Los recargos son todos multiplicativos, así que el orden da lo mismo. Eso
 *  no es pereza: la tarifa no dice en qué orden van, y con sumas SÍ importaría
 *  — habría que elegir un orden que el PDF no respalda.
 *
 *  `opciones`: { vitrina, vitrinaPalilleria, acabadoAbeto, fueraDeCarta,
 *  vetaConsecutiva, xolid, patina, poroArenado }. */
export const precioMaderaACB = (modelo, chapa, acabado, alto, ancho, opciones) => {
  const o = opciones || {};
  const m = ACB_MADERA_MODELOS.find((x) => x.id === modelo || x.nombre === modelo);
  const linea = lineaDeModeloACBMadera(modelo, chapa);
  if (!m || !linea) return null;

  // El grupo 7 (abeto tricapa) SOLO tiene crudo. Pedirle la columna B o C
  // sería tarifarlo por una tabla que no tiene.
  const col = linea.grupo === 7 ? 'crudo' : acabado;
  const base = precioBaseMaderaACB(linea.grupo, col, alto, ancho);
  if (base == null) return null;

  const chapaObj = ACB_MADERA_CHAPAS.find((c) => c.id === chapa);
  let p = base
    * (1 + linea.recargo / 100)
    * (1 + ((chapaObj && chapaObj.recargo) || 0) / 100);

  if (linea.grupo === 7 && o.acabadoAbeto) {
    const a = ACB_MADERA_ACABADOS_ABETO.find((x) => x.id === o.acabadoAbeto);
    if (!a) return null;
    p *= 1 + a.recargo / 100;
  }
  // LA VITRINA VA SOBRE EL VALOR DE LA PUERTA, y solo la llevan los once
  // modelos de la pág. 18. Palillería y celosía van a +50 % en cualquiera.
  if (o.vitrinaPalilleria) p *= 1 + ACB_MADERA_VITRINA_PALILLERIA_PCT / 100;
  else if (o.vitrina && ACB_MADERA_VITRINA_MAS_20.includes(m.nombre)) {
    p *= 1 + ACB_MADERA_VITRINA_PCT / 100;
  }
  if (o.fueraDeCarta) {
    p *= 1 + (col === 'grupoC'
      ? ACB_MADERA_PIGMENTADO_FUERA_DE_CARTA_PCT
      : ACB_MADERA_TINTE_FUERA_DE_CARTA_PCT) / 100;
  }
  if (o.patina) {
    p *= 1 + (col === 'grupoC'
      ? ACB_MADERA_PIGMENTO_PATINA_PCT
      : ACB_MADERA_TINTE_PATINA_PCT) / 100;
  }
  if (o.poroArenado) p *= 1 + ACB_MADERA_PORO_ARENADO_PCT / 100;
  if (o.vetaConsecutiva) p *= 1 + ACB_MADERA_VETA_CONSECUTIVA_PCT / 100;
  if (o.xolid) p *= 1 + ACB_MADERA_XOLID_PCT / 100;
  return Math.round(p * 100) / 100;
};

/** El escalón de costado que le toca a una superficie en cm². Sube SIEMPRE al
 *  inmediato superior; por encima del último tramo devuelve `null`, porque ACB
 *  no lo fabrica y estirar el último precio sería inventarlo.
 *
 *  `tabla` es 'robleFresno' o 'nudosNogal': SON DOS TARIFAS DISTINTAS, no una
 *  con un porcentaje encima. */
export const tramoCostadoACBMadera = (tabla, cm2) => {
  const t = ACB_MADERA_COSTADOS[tabla];
  if (!t) return null;
  const s = Number(cm2);
  if (!Number.isFinite(s) || s <= 0) return null;
  for (const fila of t) {
    const tope = Number(String(fila.hasta).match(/(\\d+)\\s*$/)[1]);
    if (s <= tope) return fila;
  }
  return null;
};''')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    RAIZ, "frontend", "src", "data", "acbMadera.js")
with open(ruta, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("escrito", ruta)
