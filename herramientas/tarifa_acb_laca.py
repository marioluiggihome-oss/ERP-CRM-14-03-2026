# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Genera frontend/src/data/acbLaca.js desde la tarifa ACB LACADOS 2026.

Transcrita del PDF oficial «TARIFA GRUPO ACB 26 V.0526165», páginas 5 a 16.

LA LACA NO SE TARIFA COMO EL CANTEADO. En el canteado el precio sale de una
matriz por serie; aquí sale de TRES pasos:

    precio = matriz(GRUPO, acabado, alto, ancho) × (1 + recargo del modelo)

El modelo dice a qué GRUPO pertenece y qué recargo lleva —y eso depende del
GRUESO: un ALZIRA de 19 mm es GRUPO 3 a secas y el de 22 mm es GRUPO 3 + 5 %—.
Después van los recargos del color y de la decoración, que se suman encima.

Se VALIDA antes de emitir nada. Un dígito mal leído en una tarifa no da ningún
error: sale en un presupuesto y se ve cuando llega la factura.
"""
import json, os, sys

COLECCION = "laca"

# ── LOS MODELOS (págs. 6 y 6 bis) ──────────────────────────────────────────
#
# (nombre, [(grueso en mm, grupo, recargo en %)], lleva_tirador_aparte)
#
# EL GRUESO MANDA EN EL PRECIO, no es una nota de fabricación: el mismo modelo
# a 19 mm y a 22 mm no vale lo mismo. Por eso cada grueso lleva su propia línea
# y no hay un «recargo por defecto» — un modelo que solo se fabrica en 22 mm
# tiene UNA línea, y pedirlo en 19 no es más barato: es que no existe.
#
# `tirador_aparte` es el asterisco de la pág. 6: «a todos los modelos con
# asterisco hay que incluirle el precio del tirador (pág. 93)». OJO: el (*) que
# aparece en las cabeceras de las matrices (págs. 8, 10 y 12) es OTRO asterisco
# —dice «consultar grueso e incrementos en pág. 6»— y no significa tirador.
# Confundirlos metería un tirador de 20 € en setenta modelos que no lo llevan.
MODELOS = [
    ("ALZIRA",             [(19, 3, 0), (22, 3, 5)], False),
    ("ANETO",              [(22, 3, 10)], False),
    ("APOLO",              [(22, 2, 5)], False),
    ("ARIZONA",            [(22, 3, 5)], False),
    ("ARLES",              [(22, 3, 5)], False),
    ("BALTIMORE",          [(22, 3, 5)], False),
    ("BERNA",              [(19, 1, 0), (22, 1, 5)], True),
    ("BOMBAY",             [(22, 3, 25)], False),
    ("CADAQUES",           [(22, 2, 5)], False),
    ("CALGARI",            [(22, 3, 25)], False),
    ("CAMBRIDGE",          [(22, 2, 5)], False),
    ("CORINTIA",           [(22, 3, 5)], False),
    ("DENVER",             [(22, 3, 5)], False),
    ("DOHA",               [(22, 3, 5)], False),
    ("DRESDE",             [(22, 2, 5)], False),
    ("DUELAS",             [(22, 3, 25)], False),
    ("EPOCA",              [(19, 3, 0), (22, 3, 5)], False),
    ("ESTOCOLMO T1",       [(22, 3, 5)], False),
    ("ESTOCOLMO T2",       [(22, 3, 5)], False),
    ("EVEREST",            [(22, 3, 10)], False),
    ("FLORENCIA",          [(22, 3, 10)], False),
    ("FLORIDA",            [(22, 3, 5)], False),
    ("GANTE TirNogal",     [(22, 2, 15)], False),
    ("GRECIA",             [(22, 3, 5)], False),
    ("HANOI",              [(22, 2, 5)], False),
    ("KANSAS",             [(22, 3, 5)], False),
    ("KANSAS Pf. Rayado",  [(22, 3, 5)], False),
    ("LAREDO",             [(22, 3, 5)], False),
    ("LEIDEN",             [(22, 1, 0)], False),
    ("LIEJA",              [(22, 3, 5)], False),
    ("LIMA",               [(22, 3, 5)], False),
    ("MADRID",             [(19, 1, 0), (22, 1, 5)], False),
    ("MAELLA T1",          [(19, 3, 0), (22, 3, 5)], False),
    ("MAELLA T2",          [(19, 3, 0), (22, 3, 5)], False),
    ("MALAGA",             [(22, 3, 0)], False),
    ("MALLORCA",           [(22, 2, 5)], False),
    ("MANACOR",            [(19, 3, 0), (22, 3, 5)], False),
    ("MARINA",             [(22, 3, 5)], False),
    ("MELBOURNE",          [(25, 3, 15)], False),
    ("MILOS",              [(22, 3, 5)], False),
    ("MONACO",             [(19, 3, 0), (22, 3, 5)], False),
    ("NANTES",             [(22, 3, 5)], False),
    ("NUBE",               [(22, 2, 5)], False),
    ("OLIMPIA",            [(22, 3, 5)], False),
    ("ONDAS 1CM",          [(22, 3, 25)], False),
    ("ONDAS 2,5CM",        [(22, 3, 25)], False),
    ("ORLANDO",            [(22, 3, 5)], False),
    ("ORLEANS",            [(22, 2, 5)], False),
    ("OSTENDE",            [(22, 3, 5)], False),
    ("OXFORD",             [(22, 3, 10)], False),
    ("PALENCIA",           [(22, 2, 5)], False),
    ("PALMA",              [(19, 2, 0), (22, 2, 5)], False),
    ("RIGA",               [(22, 3, 5)], False),
    ("RODAS",              [(22, 3, 5)], False),
    ("ROTTERDAM",          [(19, 2, 0)], False),
    ("SADA",               [(22, 3, 5)], False),
    ("SALZBURGO",          [(19, 2, 0), (22, 2, 5)], False),
    ("SILOS",              [(22, 3, 5)], False),
    ("TAPIES",             [(19, 2, 0), (22, 2, 5)], False),
    ("TEVERE",             [(30, 3, 15)], False),
    ("TRENTO",             [(22, 3, 5)], False),
    ("TREVISO",            [(22, 3, 5)], False),
    ("TRIPOLI",            [(22, 3, 5)], False),
    ("VANCOUVER",          [(22, 3, 5)], False),
    ("VARESE",             [(22, 3, 25)], False),
    ("VEGA",               [(19, 2, 0), (22, 2, 5)], False),
    ("XATIVA",             [(22, 3, 0)], False),
    ("YAKARTA",            [(22, 3, 5)], False),
    ("ZAGREB",             [(30, 3, 15)], False),
    ("ZAMORA TirNogal",    [(22, 2, 15)], False),
]

# LEIDEN SALE EN DOS GRUPOS A LA VEZ, Y ESO SON 3,59 € POR FRENTE.
#
# La pág. 6 —la tabla de modelos, que es la que manda— dice GRUPO 1, y la
# cabecera de la matriz del GRUPO 1 (pág. 8) lo confirma: «BERNA - LEIDEN -
# MADRID». Pero la cabecera del GRUPO 3 (pág. 12) TAMBIÉN lo lista, entre
# LAREDO y LIEJA, que es justo donde caería por orden alfabético en una lista
# copiada. En la casilla base son 18,40 € contra 21,99 €.
#
# Se toma el de la pág. 6 porque es la tabla de modelos, no una cabecera. Se
# deja escrito para que quien lo lea sepa que hay que confirmarlo con ACB, en
# vez de que parezca una decisión sin nada detrás.
MODELOS_EN_DOS_GRUPOS = {"LEIDEN": (1, 3)}

# ── LOS ACABADOS (las cuatro columnas de precio de cada matriz) ────────────
ACABADOS = [
    ("blancoBrillo",    "Blanco brillo"),
    ("blancoUltramatt", "Blanco ultramatt / satinado"),
    ("colorBrillo",     "Color brillo"),
    ("colorUltramatt",  "Color ultramatt / satinado"),
]

# ── LAS TRES MATRICES DE GRUPO (págs. 8-13) ────────────────────────────────
#
# (altos, anchos, {acabado: [precios en el mismo orden que los anchos]}).
#
# Un alto como «138 & 173» son DOS medidas al mismo precio: por eso `altos` es
# una lista y no un número. La rejilla es la MISMA en los tres grupos y la
# misma que en el canteado — 84 casillas, 12 bloques de alto.
MATRICES = {
    1: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [18.40,18.40,18.40,18.40,20.51,20.51,20.51,30.76,36.90,41.01,41.01,41.01],
            'blancoUltramatt': [17.46,17.46,17.46,17.46,19.44,19.44,19.44,29.21,35.05,38.95,38.95,38.95],
            'colorBrillo':   [21.23,21.24,21.24,21.24,23.66,23.66,23.66,35.51,42.61,47.36,47.36,47.36],
            'colorUltramatt': [20.18,20.17,20.17,20.17,22.48,22.48,22.48,33.73,40.48,44.98,44.98,44.98],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [32.37,33.76,33.76,35.18,35.18,35.18,41.18,51.83,62.50,78.10,93.57],
            'blancoUltramatt': [30.76,32.07,32.07,33.41,33.41,33.41,39.13,49.26,59.39,74.22,88.86],
            'colorBrillo':   [37.37,39.01,39.01,40.62,40.62,40.62,47.52,59.88,72.22,90.28,108.04],
            'colorUltramatt': [35.52,37.06,37.06,38.42,38.42,38.42,45.17,56.88,68.58,85.76,102.63],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [33.37,35.58,35.58,37.82,37.82,37.82,42.58,54.92,67.26],
            'blancoUltramatt': [31.70,33.81,33.81,35.94,35.94,35.94,40.45,52.18,63.90],
            'colorBrillo':   [38.54,41.11,41.11,43.68,43.68,43.68,49.16,63.43,77.68],
            'colorUltramatt': [36.61,39.04,39.04,41.50,41.50,41.50,46.71,60.25,73.80],
        }),
        ([418], [298, 598], {
            'blancoBrillo':  [35.58,50.43],
            'blancoUltramatt': [33.81,47.89],
            'colorBrillo':   [41.11,58.22],
            'colorUltramatt': [39.04,55.30],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [41.01,42.03,43.60,44.64,46.77,53.08,53.57,74.21,74.21],
            'blancoUltramatt': [38.94,39.92,41.43,42.41,44.44,50.41,50.89,70.68,70.68],
            'colorBrillo':   [47.35,48.56,50.36,51.59,54.05,61.28,61.91,85.90,85.90],
            'colorUltramatt': [44.99,46.08,47.86,48.98,51.33,58.21,58.78,81.61,81.61],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [41.01,41.01,42.03,43.60,44.64,46.77,53.08],
            'blancoUltramatt': [38.94,38.94,39.92,41.43,42.41,44.44,50.41],
            'colorBrillo':   [47.35,47.35,48.56,50.36,51.59,54.05,61.28],
            'colorUltramatt': [44.99,44.99,46.08,47.86,48.98,51.33,58.21],
        }),
        ([598], [598], {
            'blancoBrillo':  [62.51],
            'blancoUltramatt': [59.38],
            'colorBrillo':   [72.21],
            'colorUltramatt': [68.58],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [41.18,41.18,42.58,44.64,48.86,53.08,62.52],
            'blancoUltramatt': [39.13,39.13,40.45,42.41,46.44,50.41,59.39],
            'colorBrillo':   [47.53,47.53,49.16,51.59,56.44,61.28,72.22],
            'colorUltramatt': [45.17,45.17,46.70,48.98,53.61,58.21,68.58],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [61.27,61.27,65.91,67.00,72.71,78.89,84.33],
            'blancoUltramatt': [58.20,58.20,62.62,63.66,69.27,74.98,80.11],
            'colorBrillo':   [70.77,70.78,76.13,77.40,84.18,91.15,97.38],
            'colorUltramatt': [67.21,67.21,72.32,73.53,79.97,86.57,92.52],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [62.52,62.52,67.26,68.36,74.20,80.50,86.05],
            'blancoUltramatt': [59.39,59.39,63.90,64.96,70.68,76.51,81.75],
            'colorBrillo':   [72.22,72.22,77.68,78.97,85.90,93.01,99.36],
            'colorUltramatt': [68.58,68.58,73.80,75.03,81.61,88.34,94.41],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [93.57,93.57,93.57,104.57,120.86,120.86],
            'blancoUltramatt': [88.85,88.85,88.85,99.35,114.80,114.80],
            'colorBrillo':   [108.05,108.05,108.05,120.76,139.58,139.58],
            'colorUltramatt': [102.63,102.63,102.63,114.71,132.60,132.60],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [103.68,109.84,113.01,123.07,133.57,148.56],
            'blancoUltramatt': [98.49,104.34,107.35,116.91,126.89,141.12],
            'colorBrillo':   [119.74,119.74,130.52,142.13,154.27,171.57],
            'colorUltramatt': [113.74,113.74,123.99,135.01,146.54,162.99],
        }),
    ],
    2: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [19.98,19.98,19.98,19.98,22.26,22.26,22.26,33.39,40.07,44.52,44.52,44.52],
            'blancoUltramatt': [18.98,18.98,18.98,18.98,21.17,21.17,21.17,31.77,38.13,42.36,42.36,42.36],
            'colorBrillo':   [23.09,23.09,23.09,23.09,25.72,25.72,25.72,38.57,46.30,51.44,51.44,51.44],
            'colorUltramatt': [21.93,21.93,21.93,21.93,24.42,24.42,24.42,36.63,43.95,48.84,48.84,48.84],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [35.18,36.71,36.71,38.23,38.23,38.23,44.75,56.36,67.97,84.96,101.69],
            'blancoUltramatt': [33.41,34.87,34.87,36.33,36.33,36.33,42.51,53.52,64.54,80.70,96.60],
            'colorBrillo':   [40.63,42.40,42.40,44.18,44.18,44.18,51.70,65.10,78.49,98.11,117.42],
            'colorUltramatt': [38.61,40.30,40.30,41.96,41.96,41.96,49.09,61.83,74.57,93.20,111.55],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [36.27,38.67,38.67,41.11,41.11,41.11,46.29,59.68,73.08],
            'blancoUltramatt': [34.45,36.75,36.75,39.05,39.05,39.05,43.95,56.69,69.45],
            'colorBrillo':   [41.90,44.68,44.68,47.47,47.47,47.47,53.45,68.95,84.43],
            'colorUltramatt': [39.79,42.45,42.45,45.10,45.10,45.10,50.76,65.49,80.22],
        }),
        ([418], [298, 598], {
            'blancoBrillo':  [38.67,54.79],
            'blancoUltramatt': [36.75,52.05],
            'colorBrillo':   [44.68,63.30],
            'colorUltramatt': [42.45,60.13],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [44.54,45.69,47.40,48.55,50.85,57.67,58.26,80.88,80.88],
            'blancoUltramatt': [42.33,43.41,45.04,46.08,48.28,54.79,55.30,76.81,76.81],
            'colorBrillo':   [51.46,52.75,54.77,56.04,58.74,66.63,67.25,93.38,93.38],
            'colorUltramatt': [48.89,50.14,52.01,53.26,55.78,63.30,63.91,88.71,88.71],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [44.54,44.54,45.69,47.40,48.55,50.85,57.67],
            'blancoUltramatt': [42.33,42.33,43.41,45.04,46.08,48.28,54.79],
            'colorBrillo':   [51.46,51.46,52.75,54.77,56.04,58.74,66.63],
            'colorUltramatt': [48.89,48.89,50.14,52.01,53.26,55.78,63.30],
        }),
        ([598], [598], {
            'blancoBrillo':  [67.95],
            'blancoUltramatt': [64.54],
            'colorBrillo':   [78.49],
            'colorUltramatt': [74.57],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [44.75,44.75,46.29,48.55,53.12,57.67,67.95],
            'blancoUltramatt': [42.51,42.51,43.95,46.08,50.45,54.79,64.54],
            'colorBrillo':   [51.70,51.70,53.45,56.04,61.32,66.63,78.49],
            'colorUltramatt': [49.09,49.09,50.76,53.26,58.28,63.30,74.57],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [66.59,66.59,71.62,72.85,79.26,85.76,91.66],
            'blancoUltramatt': [63.25,63.25,68.04,69.19,75.26,81.49,87.07],
            'colorBrillo':   [76.92,76.92,82.75,84.12,91.51,99.03,105.84],
            'colorUltramatt': [73.08,73.08,78.62,79.91,86.94,94.11,100.56],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [67.95,67.95,73.08,74.34,80.87,87.51,93.53],
            'blancoUltramatt': [64.54,64.54,69.43,70.60,76.80,83.15,88.85],
            'colorBrillo':   [78.49,78.49,84.43,85.84,93.38,101.05,108.00],
            'colorUltramatt': [74.57,74.57,80.22,81.54,88.71,96.03,102.61],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [101.69,101.69,101.69,114.07,131.36,131.36],
            'blancoUltramatt': [96.60,96.60,96.60,107.98,124.79,124.79],
            'colorBrillo':   [117.43,117.43,117.43,131.24,151.74,151.74],
            'colorUltramatt': [111.56,111.56,111.56,124.71,144.16,144.16],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [112.69,119.38,122.89,128.66,145.19,161.46],
            'blancoUltramatt': [107.05,113.40,116.75,122.23,137.93,153.38],
            'colorBrillo':   [130.15,137.88,141.93,148.59,167.69,186.49],
            'colorUltramatt': [123.64,130.97,134.80,141.15,159.29,177.16],
        }),
    ],
    3: [
        ([138, 173], [248, 298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [21.99,21.99,21.99,21.99,24.49,24.49,24.49,36.74,44.07,48.98,48.98,48.98],
            'blancoUltramatt': [20.88,20.88,20.88,20.88,23.26,23.26,23.26,34.89,41.86,46.53,46.53,46.53],
            'colorBrillo':   [25.39,25.39,25.39,25.39,28.28,28.28,28.28,42.42,50.89,56.57,56.57,56.57],
            'colorUltramatt': [24.12,24.12,24.12,24.12,26.88,26.88,26.88,40.28,48.50,53.74,53.74,53.74],
        }),
        ([278], [298, 348, 398, 448, 498, 598, 698, 798, 898, 998, 1198], {
            'blancoBrillo':  [38.69,40.38,40.38,42.08,42.08,42.08,49.24,61.98,74.75,93.45,111.83],
            'blancoUltramatt': [36.77,38.38,38.38,39.97,39.97,39.97,46.75,58.88,71.02,88.77,106.25],
            'colorBrillo':   [44.68,46.63,46.63,48.61,48.61,48.61,56.85,71.59,86.34,107.92,129.21],
            'colorUltramatt': [42.45,44.29,44.29,46.15,46.15,46.15,54.02,68.01,82.00,102.49,122.71],
        }),
        ([348], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [39.90,42.56,42.56,45.21,45.21,45.21,50.91,65.67,80.41],
            'blancoUltramatt': [37.90,40.43,40.43,42.95,42.95,42.95,48.34,62.37,76.40],
            'colorBrillo':   [46.06,49.13,49.13,52.20,52.20,52.20,58.80,75.84,92.88],
            'colorUltramatt': [43.76,46.68,46.68,49.62,49.62,49.62,55.84,72.05,88.25],
        }),
        ([418], [298, 598], {
            'blancoBrillo':  [42.56,60.28],
            'blancoUltramatt': [40.43,57.27],
            'colorBrillo':   [49.13,69.63],
            'colorUltramatt': [46.68,66.13],
        }),
        ([448], [298, 348, 398, 448, 498, 598, 698, 798, 898], {
            'blancoBrillo':  [49.01,50.68,52.16,53.37,55.94,63.46,70.09,88.93,88.93],
            'blancoUltramatt': [46.56,47.76,49.53,50.72,53.12,60.28,66.60,84.48,84.48],
            'colorBrillo':   [56.61,58.04,60.23,61.68,64.59,73.30,80.98,102.70,102.70],
            'colorUltramatt': [53.76,55.12,57.20,58.58,61.37,69.61,76.93,97.60,97.60],
        }),
        ([558], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [49.01,49.01,50.68,52.16,53.37,55.94,63.46],
            'blancoUltramatt': [46.56,46.56,47.76,49.53,50.72,53.12,60.28],
            'colorBrillo':   [56.61,56.61,58.04,60.23,61.68,64.59,73.30],
            'colorUltramatt': [53.76,53.76,55.12,57.20,58.58,61.37,69.61],
        }),
        ([598], [598], {
            'blancoBrillo':  [74.75],
            'blancoUltramatt': [71.02],
            'colorBrillo':   [86.34],
            'colorUltramatt': [82.02],
        }),
        ([698], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [49.24,49.24,50.91,53.37,58.40,63.46,74.75],
            'blancoUltramatt': [46.75,46.75,48.34,50.70,55.50,60.28,71.02],
            'colorBrillo':   [56.85,56.85,58.80,61.68,67.49,73.30,86.34],
            'colorUltramatt': [54.02,54.02,55.84,58.58,64.11,69.61,82.02],
        }),
        ([798], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [73.26,73.26,78.80,80.11,87.15,94.32,100.80],
            'blancoUltramatt': [69.60,69.60,74.88,76.10,82.80,89.63,95.77],
            'colorBrillo':   [84.61,84.61,91.02,92.52,100.64,108.96,116.44],
            'colorUltramatt': [80.38,80.38,86.48,87.90,95.64,103.50,110.63],
        }),
        ([898], [248, 298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [74.75,74.75,80.41,81.75,88.93,96.24,102.86],
            'blancoUltramatt': [71.02,71.02,76.40,77.66,84.49,91.46,97.72],
            'colorBrillo':   [86.34,86.34,92.88,94.41,102.70,111.18,118.81],
            'colorUltramatt': [82.02,82.02,88.25,89.70,97.59,105.61,112.89],
        }),
        ([1198, 1298], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [111.84,111.84,111.84,124.99,144.50,144.50],
            'blancoUltramatt': [106.24,106.24,106.24,118.77,137.27,137.27],
            'colorBrillo':   [129.21,129.21,129.21,144.40,166.89,166.89],
            'colorUltramatt': [122.72,122.72,122.72,137.16,158.54,158.54],
        }),
        ([1498, 1598], [298, 348, 398, 448, 498, 598], {
            'blancoBrillo':  [123.99,131.33,135.13,147.33,159.70,177.62],
            'blancoUltramatt': [117.78,124.76,128.37,139.96,151.71,168.74],
            'colorBrillo':   [143.20,151.67,156.07,170.15,184.44,205.12],
            'colorUltramatt': [136.02,144.07,148.25,161.64,175.20,194.85],
        }),
    ],
}

# ── LOS COLORES (pág. 7) ───────────────────────────────────────────────────
#
# Los ESPECIALES no son «otro color»: se tarifan sobre el precio de BLANCO con
# un 25 % encima, no sobre el de color. Con el blanco brillo del grupo 1 en
# 18,40 €, un microarenado sale a 23,00 € y no a 26,54 €, que es lo que daría
# aplicárselo al de color. Por eso los porcentajes viven aquí y no escritos a
# mano en una pantalla.
COLORES_ESTANDAR = ['AGUA MARINA', 'ALGA', 'ALUMINIO', 'AMAPOLA', 'ANTARTIDA', 'ANTRACITA', 'ARDILLA', 'ARENA', 'ARIDO', 'AYURE', 'AZUL ARMONIA', 'AZUL CARIBE', 'AZUL OXFORD', 'AZUL REAL', 'BEIGE', 'BEIGE GRISACEO', 'BLANCO', 'BLANCO ROTO', 'BLANCO RUSTICO', 'BOSQUE', 'BURDEOS', 'CAMEL', 'CANELA', 'CARIOCA', 'CASTAÑO', 'CAVA', 'CENIZA', 'CEREZA', 'CHOCOLATE', 'CIELO', 'COBRE', 'COCO', 'CORZO', 'CRISTALINO', 'CURRY', 'DESIERTO', 'DORADO', 'EGEO', 'GOLD', 'GRAFITO', 'GRANATE', 'GREEN', 'GRIS', 'GRIS NEUTRO', 'GRIS PERLA', 'GRIS PLOMO', 'GRIS TAMAKI', 'GRUS VITBER', 'HUESO Nº10', 'HUESO Nº8', 'LAGO', 'LANDALO', 'LINO', 'LONDON GREY', 'LUNA', 'MAGNOLIA', 'MARENGO', 'MARFIL', 'MARTE', 'MEDITERRANEO', 'MENTA', 'MERENGUE', 'MOSTAZA', 'MUSGO', 'NEGRO', 'NIGU', 'NUBE', 'NÍSPERO', 'OCEANO', 'OLIVE', 'ORO', 'OTOÑO', 'PAPER CREAM', 'PASTEL', 'PERGAMON Nº1', 'PIEDRA ARENA', 'PIEDRA BEIGE', 'PIEDRA GRAFITO', 'PIEDRA GRIS', 'PIGEON', 'PISTACHO', 'PIZARRA', 'PLATA', 'PLOMO', 'PORCELANA', 'PRIMAVERA', 'RIOJA', 'ROJO', 'ROJO TINTO', 'ROSA CARAMELO', 'SAHARA', 'SILICE', 'SMOKE', 'SOMBRA', 'STONE', 'TERRA', 'TERRACOTA', 'TERROSA', 'TEXAS', 'TINTO', 'TITANIO', 'TOFFE', 'TOPO', 'TREBOL', 'TURQUESA', 'VANILA', 'VERDE AZULADO', 'VERDE CLARO', 'VERDE FONTANA', 'VIOLETA', 'VISON', 'VULCANO', 'YESO']

COLORES_ESPECIALES = ['MICROARENADO BONE', 'MICROARENADO DARK GREEN', 'MICROARENADO DESERT', 'MICROARENADO GREY', 'MICROARENADO IGNEO', 'MICROARENADO LAVA', 'MICROARENADO SAND', 'MICROARENADO SIENA']

DECORACIONES = [('ARISTA VIVA', 5), ('FILO CROMADO', 10), ('FILO ORO', 10), ('INOX METAL COBRE', 18), ('INOX METAL PLATA', 18), ('METALIZADO', 10), ('METAL ACERO', 18), ('METAL ORO', 18), ('PATINADO', 10)]
# ── COMPLEMENTOS, DISEÑO Y COSTADOS (págs. 14, 15 y 16) ────────────────────
#
# Los complementos van por PIEZA (una cornisa, un portaluz, una campana), con
# las mismas cuatro columnas de acabado que los frentes. Los costados van por
# SUPERFICIE en cm² y llevan SEIS columnas, porque ahí el color especial tiene
# su propia columna en vez de calcularse.
COMPLEMENTOS = [
    ('CORNISA PLANA', [67.8, 64.4, 78.29, 74.39]),
    ('CORNISA REDONDA', [65.3, 62.04, 75.42, 71.63]),
    ('CORNISA DISEÑO', [91.38, 86.82, 105.55, 100.26]),
    ('PORTALUZ', [56.84, 54.0, 65.67, 62.38]),
    ('PORTALUZ DISEÑO', [81.71, 77.59, 94.37, 89.65]),
    ('ZOCALO DE 15', [43.6, 41.43, 50.36, 47.86]),
    ('FRENTE HORNO 75X598', [10.34, 9.84, 11.95, 11.36]),
    ('REGLETA 698X98', [10.92, 10.38, 12.61, 11.97]),
    ('REGLETA 900X98', [14.49, 13.76, 16.73, 15.87]),
    ('REGLETA 1940X98', [31.24, 29.67, 36.09, 34.27]),
    ('COSTADO 2440X600X19', [125.32, 119.05, 144.73, 137.5]),
    ('COSTADO 2 CARAS 2440X600X19', [164.73, 156.49, 190.24, 180.75]),
    ('PANEL 2440X600X4', [54.5, 51.76, 62.95, 59.77]),
    ('DECORATIVO 3B 700X300X300', [81.08, 77.01, 93.64, 88.95]),
    ('DECORATIVO 4B 900X300X300', [105.58, 100.31, 121.95, 115.83]),
    ('BOTELLERO 5B 700X300X300', [98.29, 93.36, 113.51, 107.83]),
    ('BOTELLERO 6B 900X300X300', [122.66, 116.54, 141.68, 134.62]),
    ('CAMPANA TRAPECIO', [541.41, 514.34, 625.35, 594.04]),
    ('CAMPANA DISEÑO A', [912.28, 866.67, 1101.59, 1046.42]),
    ('CAMPANA DISEÑO B', [709.96, 674.27, 819.76, 782.51]),
    ('CAMPANA DISEÑO C', [709.96, 674.27, 819.76, 782.51]),
    ('CAMPANA DISEÑO D', [709.96, 674.27, 819.76, 782.51]),
    ('CAMPANA DISEÑO E', [709.96, 674.27, 819.76, 782.51]),
    ('CAMPANA DISEÑO F', [892.01, 847.41, 1077.1, 1023.23]),
]

DISENO_ULTRAMATT = [
    ('REGLETA DISEÑO Nº 3 700X98 PIRAMIDE', [23.03, 31.46]),
    ('REGLETA DISEÑO Nº 3 900X98 PIRAMIDE', [29.61, 40.46]),
    ('REGLETA DISEÑO Nº 3 1940X98 PIRAMIDE', [48.34, 66.09]),
    ('COLUMNA DISEÑO CLÁSICO 700', [89.75, 106.22]),
    ('COLUMNA DISEÑO CLÁSICO 900', [106.45, 125.97]),
    ('COLUMNA DISEÑO CLÁSICO 1940', [266.62, 315.54]),
]

CURVAS = [
    ('CURVAS PARA TERMINAL DISEÑO LISO', [('ALTO HASTA 70 CM', [148.71, 141.27, 171.76, 163.17]), ('ALTO HASTA 90 CM', [182.39, 173.27, 210.66, 200.13]), ('ALTO HASTA 130 CM', [241.55, 229.47, 278.99, 265.04]), ('ALTO HASTA 200 CM', [351.87, 334.28, 406.42, 386.09])]),
    ('CURVAS PARA TERMINAL DISEÑO CON MOLDURA', [('ALTO HASTA 70 CM', [257.55, 269.66, 285.78, 310.03]), ('ALTO HASTA 90 CM', [293.35, 307.78, 325.85, 353.57]), ('ALTO HASTA 130 CM', [344.11, 360.73, 382.34, 414.97]), ('ALTO HASTA 150 CM', [396.06, 415.31, 440.34, 478.0]), ('ALTO HASTA 200 CM', [446.73, 468.86, 497.25, 539.86])]),
    ('CURVAS PARA TERMINAL DISEÑO CON MOLDURA PARA ISLA DE 90 DE ANCHO (2 PUERTAS)', [('ALTO HASTA 70 CM', [285.26, 296.49, 302.64, 336.65]), ('ALTO HASTA 90 CM', [320.15, 334.46, 351.71, 380.58])]),
]

RETRO = [('MUEBLE RETRO (ALTO) 700', [242.78, 230.64, 280.41, 266.39]), ('MUEBLE RETRO (BAJO) 700', [351.11, 333.55, 405.53, 385.25]), ('PUERTA RETRO 700X600', [70.04, 66.54, 80.89, 76.85]), ('MUEBLE RETRO (ALTO) 900', [265.83, 252.54, 307.03, 291.68]), ('PUERTA RETRO 900X600', [96.34, 91.52, 266.79, 253.45])]

COSTADOS_UNA_CARA = [
    ('HASTA 2000', [21.07, 20.02, 24.33, 23.11, 26.34, 25.02]),
    ('HASTA 2500', [26.29, 24.97, 30.39, 28.84, 32.89, 31.24]),
    ('HASTA 3000', [31.37, 29.97, 36.44, 34.6, 39.45, 37.47]),
    ('HASTA 3500', [36.88, 35.04, 42.59, 40.48, 46.1, 43.79]),
    ('HASTA 4000', [42.15, 40.04, 48.67, 46.27, 52.69, 50.07]),
    ('HASTA 4500', [47.37, 45.02, 54.72, 52.0, 59.23, 56.27]),
    ('HASTA 5000', [52.69, 50.07, 60.82, 57.81, 65.85, 62.56]),
    ('HASTA 5500', [57.93, 55.02, 66.9, 63.57, 72.41, 68.79]),
    ('HASTA 6000', [63.15, 59.99, 72.93, 69.3, 78.96, 75.01]),
    ('HASTA 6500', [68.42, 65.01, 79.03, 75.09, 85.53, 81.26]),
    ('HASTA 7000', [73.71, 70.01, 85.13, 80.87, 92.14, 87.51]),
    ('HASTA 7500', [79.01, 75.06, 91.26, 86.68, 98.76, 93.81]),
    ('HASTA 8000', [84.25, 80.06, 97.31, 92.46, 105.33, 100.06]),
    ('HASTA 8500', [90.18, 85.65, 104.12, 98.93, 112.73, 107.07]),
    ('HASTA 9000', [94.79, 90.03, 109.47, 104.0, 118.49, 112.55]),
    ('HASTA 9500', [100.03, 95.03, 115.52, 109.76, 125.03, 118.78]),
    ('HASTA 10000', [105.3, 100.03, 121.62, 115.54, 131.64, 125.05]),
    ('HASTA 10500', [110.62, 105.08, 127.79, 121.35, 138.26, 131.35]),
    ('DE 11000 A 14640', [125.32, 119.05, 144.73, 137.5, 156.64, 148.82]),
]

COSTADOS_DOS_CARAS = [
    ('HASTA 2000', [27.64, 26.27, 31.93, 30.36, 34.55, 32.84]),
    ('HASTA 2500', [34.58, 32.86, 39.94, 37.96, 43.23, 41.05]),
    ('HASTA 3000', [41.49, 39.43, 47.91, 45.51, 51.85, 49.26]),
    ('HASTA 3500', [48.42, 46.0, 55.95, 53.13, 60.53, 57.49]),
    ('HASTA 4000', [55.33, 52.54, 63.91, 60.72, 69.18, 65.7]),
    ('HASTA 4500', [62.27, 59.16, 71.92, 68.32, 77.83, 73.93]),
    ('HASTA 5000', [69.18, 65.7, 79.89, 75.89, 82.7, 82.14]),
    ('HASTA 5500', [76.08, 72.27, 87.88, 83.47, 95.08, 90.35]),
    ('HASTA 6000', [82.98, 78.84, 95.84, 91.06, 103.73, 98.56]),
    ('HASTA 6500', [89.91, 85.43, 103.86, 98.66, 112.38, 106.8]),
    ('HASTA 7000', [96.85, 91.99, 111.87, 106.28, 121.06, 115.03]),
    ('HASTA 7500', [103.78, 98.59, 119.86, 113.88, 129.73, 123.07]),
    ('HASTA 8000', [110.67, 105.13, 127.82, 121.43, 138.34, 131.4]),
    ('HASTA 8500', [117.58, 111.67, 135.79, 129.0, 146.96, 139.61]),
    ('HASTA 9000', [124.49, 118.29, 143.8, 136.6, 155.66, 147.84]),
    ('HASTA 9500', [131.4, 124.83, 151.76, 144.17, 164.26, 156.05]),
    ('HASTA 10000', [140.12, 133.12, 161.84, 153.75, 175.14, 166.39]),
    ('HASTA 10500', [145.25, 113.58, 167.74, 159.36, 181.56, 172.5]),
    ('DE 11000 A 14640', [164.73, 156.49, 190.24, 180.75, 205.9, 195.6]),
]

# Los seis acabados de la tabla de costados (pág. 16). Son SEIS y no cuatro:
# el color especial tiene ahí su propia columna, así que en costados NO se
# aplica el 25 % — ya viene aplicado. Calcularlo encima sería cobrarlo dos
# veces.
ACABADOS_COSTADO = [
    ("blancoBrillo",     "Blanco brillo"),
    ("blancoMate",       "Blanco mate / satinado"),
    ("colorBrillo",      "Color brillo"),
    ("colorMate",        "Color mate / satinado"),
    ("especialBrillo",   "Color especial brillo"),
    ("especialMate",     "Color especial mate / satinado"),
]

# ── LAS REGLAS QUE VIENEN ESCRITAS EN LA TARIFA ────────────────────────────
COLOR_ESPECIAL_PCT = 0.25   # pág. 7: «sobre el precio de blanco en un 25%»
XOLID_PCT          = 0.15   # pág. 7: «Acabado XOLID: 15% sobre tarifa mate»
COSTADO_22MM_PCT   = 0.10   # pág. 16
COSTADO_30MM_PCT   = 0.25   # pág. 16
COSTADO_ALIGERADO_PCT = 0.50  # pág. 16, grueso 5 cm
COSTADO_ATAMBORADO_M2 = 304.19  # pág. 16, € /m² sobre color o blanco
JUNQUILLOS_VITRINA = 10.88  # €/und., págs. 7 y 14
PANEL_MUESTRAS     = 16.32  # € netos, 200x200x4, solo colores especiales
# pág. 7: «El precio para medidas especiales será igual al precio de la medida
# inmediata superior». No se interpola NUNCA: se sube al escalón siguiente.
MEDIDA_ESPECIAL = "sube a la medida inmediata superior"

# ── ANOMALÍAS DE LA TARIFA, COMPROBADAS CONTRA EL PDF ──────────────────────
#
# Aquí solo entra lo que se ha mirado y ha resultado ser así de verdad en el
# PDF. Se copia lo que ACB factura, no lo que debería facturar (CLAUDE.md,
# regla 7: no se inventa un número). Es una LISTA CERRADA: una anomalía nueva
# pone la validación en rojo, que es justo lo que se busca.
#
# 1. Costado a DOS CARAS, blanco mate, «HASTA 10500»: 113,58 € cuando el de
#    10000 vale 133,12 € y el de 9500 vale 124,83 €. Una pieza más grande por
#    menos dinero — casi seguro un dígito de ACB, pero no se corrige a ojo.
# 2. PUERTA RETRO 900X600 en color: 266,79 € contra 96,34 € en blanco. Todas
#    las demás filas de esa tabla van a ×1,155.
# 3. Costado a DOS CARAS, color especial brillo, «HASTA 5000»: 82,70 €, cuando
#    por el paso de la columna tocarían ~86,5 €. No rompe el orden, así que no
#    salta solo; se deja anotado.
# 4. Curvas para terminal CON MOLDURA: ahí la tarifa INVIERTE brillo y
#    ultramatt —el ultramatt cuesta más— en las nueve filas de las dos tablas
#    con moldura. Al ser las nueve, no es un dígito suelto.
ANOMALIA_COSTADO_2C_10500 = ("dosCaras", "HASTA 10500", "blancoMate")
ANOMALIA_PUERTA_RETRO_900 = "PUERTA RETRO 900X600"
CURVAS_CON_MOLDURA_INVIERTEN = tuple(
    g for g, _ in CURVAS if "MOLDURA" in g)


# ── VALIDACIÓN ─────────────────────────────────────────────────────────────
# Un céntimo de tolerancia, igual que en el canteado: lo que se caza son
# dígitos mal leídos, y esos fallan por decenas, no por céntimos.
TOL = 0.011
fallos = []
IDS = [a for a, _ in ACABADOS]

# 1. La rejilla es la misma en los tres grupos.
forma = [(a, w) for a, w, _ in MATRICES[1]]
for g in (2, 3):
    if [(a, w) for a, w, _ in MATRICES[g]] != forma:
        fallos.append(f"el grupo {g} no tiene la misma rejilla que el grupo 1")

for g, bloques in MATRICES.items():
    for altos, anchos, precios in bloques:
        for aid in IDS:
            vals = precios[aid]
            if len(vals) != len(anchos):
                fallos.append(f"G{g} {altos} {aid}: {len(vals)} precios para "
                              f"{len(anchos)} anchos")
                continue
            # 2. Dentro de un alto, el precio sube con el ancho.
            for (w1, v1), (w2, v2) in zip(zip(anchos, vals), list(zip(anchos, vals))[1:]):
                if v1 - v2 > TOL:
                    fallos.append(f"G{g} alto {altos} {aid}: {w2} ({v2}) "
                                  f"cuesta menos que {w1} ({v1})")
        # 3. El brillo cuesta más que el ultramatt, y el color más que el blanco.
        for i, w in enumerate(anchos):
            bb, bu = precios["blancoBrillo"][i], precios["blancoUltramatt"][i]
            cb, cu = precios["colorBrillo"][i], precios["colorUltramatt"][i]
            if bu - bb > TOL:
                fallos.append(f"G{g} {altos}x{w}: blanco ultramatt ({bu}) "
                              f"cuesta más que brillo ({bb})")
            if cu - cb > TOL:
                fallos.append(f"G{g} {altos}x{w}: color ultramatt ({cu}) "
                              f"cuesta más que brillo ({cb})")
            if bb - cb > TOL:
                fallos.append(f"G{g} {altos}x{w}: el color ({cb}) cuesta menos "
                              f"que el blanco ({bb})")

# 4. Y los grupos suben: 1 ≤ 2 ≤ 3 en la MISMA casilla. Es lo que hace que el
#    grupo signifique algo; si se cruzaran, una columna estaría desplazada.
for i, (altos, anchos, _) in enumerate(MATRICES[1]):
    for j, w in enumerate(anchos):
        for aid in IDS:
            v = [MATRICES[g][i][2][aid][j] for g in (1, 2, 3)]
            if not (v[0] - TOL <= v[1] and v[1] - TOL <= v[2]):
                fallos.append(f"{altos}x{w} {aid}: los grupos no suben {v}")

# 5. Los modelos: grupo conocido, recargo razonable, sin repetir grueso.
for nombre, lineas, _ in MODELOS:
    if not lineas:
        fallos.append(f"{nombre} no dice en qué grupo está")
    gruesos = [g for g, _, _ in lineas]
    if len(gruesos) != len(set(gruesos)):
        fallos.append(f"{nombre} repite un grueso: {gruesos}")
    for grueso, grupo, recargo in lineas:
        if grupo not in MATRICES:
            fallos.append(f"{nombre} de {grueso}mm dice grupo {grupo}, que no existe")
        if not (10 <= grueso <= 40):
            fallos.append(f"{nombre}: un grueso de {grueso}mm no es una puerta")
        if not (0 <= recargo <= 30):
            fallos.append(f"{nombre} de {grueso}mm lleva un {recargo}% de recargo")

# 6. Complementos y costados: nada gratis, y el costado sube con la superficie.
for nombre, vals in COMPLEMENTOS:
    if len(vals) != 4:
        fallos.append(f"complemento {nombre}: {len(vals)} precios, tocan 4")
    for v in vals:
        if not (1 <= v <= 2000):
            fallos.append(f"complemento {nombre} a {v} €, fuera de todo rango")
for cara, tabla in (("unaCara", COSTADOS_UNA_CARA), ("dosCaras", COSTADOS_DOS_CARAS)):
    for k, (aid, _) in enumerate(ACABADOS_COSTADO):
        for (n1, v1), (n2, v2) in zip(tabla, tabla[1:]):
            if v1[k] - v2[k] > TOL and (cara, n2, aid) != ANOMALIA_COSTADO_2C_10500:
                fallos.append(f"costado {cara}/{aid}: {n2} ({v2[k]}) cuesta "
                              f"menos que {n1} ({v1[k]})")

if fallos:
    print("REVISAR la transcripción de la laca:")
    for f in fallos:
        print("  ", f)
    raise SystemExit(1)

n = sum(len(v) for bs in MATRICES.values() for _, _, p in bs for v in p.values())
print("✓ validado: rejilla igual en los tres grupos, el precio sube con el "
      "ancho, el color cuesta más que el blanco y los grupos van de menos a más")
print(f"  modelos: {len(MODELOS)} · precios de matriz: {n} · "
      f"colores: {len(COLORES_ESTANDAR)} estándar + {len(COLORES_ESPECIALES)} especiales")


# ── EMITIR EL FICHERO ──────────────────────────────────────────────────────
def js(o):
    return json.dumps(o, ensure_ascii=False)


def ident(nombre):
    """El id con el que viaja un modelo. Se deriva del nombre para que no haya
    que mantener dos listas; los espacios y las comas no valen en una clave."""
    return (nombre.replace(" ", "_").replace(".", "").replace(",", "_"))


out = ['''/*
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
// se negocia y cambia (igual que en los cascos y en el canteado).''']

out.append("""
/** Las cuatro columnas de precio de cada matriz de grupo. */
export const ACB_LACA_ACABADOS = %s;

/** Y los seis de la tabla de COSTADOS, que son otros: allí el color especial
 *  tiene columna propia, así que sobre un costado NO se aplica el 25 %% — ya
 *  viene aplicado, y sumarlo sería cobrarlo dos veces. */
export const ACB_LACA_ACABADOS_COSTADO = %s;""" % (
    js([{"id": a, "label": l} for a, l in ACABADOS]),
    js([{"id": a, "label": l} for a, l in ACABADOS_COSTADO])))

out.append("""
/** LOS MODELOS (págs. 6 y 6 bis).
 *
 *  `lineas` es una por GRUESO, porque el grueso manda en el precio: el mismo
 *  modelo a 19 y a 22 mm no vale lo mismo. Un modelo que solo tiene una línea
 *  SOLO SE FABRICA en ese grueso — pedirlo en otro no es más barato, es que no
 *  existe.
 *
 *  `tiradorAparte` es el asterisco de la pág. 6: hay que sumarle el precio del
 *  tirador (pág. 93, en `acbPuertas.js`). */
export const ACB_LACA_MODELOS = [""")
for nombre, lineas, tir in MODELOS:
    out.append("  { id: %s, nombre: %s, tiradorAparte: %s, lineas: %s }," % (
        js(ident(nombre)), js(nombre), js(tir),
        js([{"grueso": g, "grupo": gr, "recargo": rc} for g, gr, rc in lineas])))
out.append("];\n")

out.append("""/** LEIDEN sale en dos grupos a la vez en la tarifa de ACB. Se toma el de la
 *  pág. 6 (la tabla de modelos, que es la que manda); la cabecera de la matriz
 *  del grupo 3 también lo lista. Son 3,59 € por frente en la casilla base, así
 *  que conviene confirmarlo con el proveedor en vez de dejarlo sin decir. */
export const ACB_LACA_MODELOS_EN_DOS_GRUPOS = %s;""" % js(
    {k: list(v) for k, v in MODELOS_EN_DOS_GRUPOS.items()}))

out.append("""
/** LAS TRES MATRICES DE GRUPO (págs. 8 a 13), en MILÍMETROS.
 *  Un alto como «138 & 173» son DOS medidas al mismo precio: por eso `altos`
 *  es una lista y no un número. */
export const ACB_LACA_MATRICES = {""")
for g in sorted(MATRICES):
    out.append("  %d: [" % g)
    for altos, anchos, precios in MATRICES[g]:
        out.append("    { altos: %s, anchos: %s, precios: %s }," % (
            js(altos), js(anchos), js(precios)))
    out.append("  ],")
out.append("};\n")

out.append("""/** LOS COLORES (pág. 7).
 *
 *  Los ESPECIALES no son «otro color»: se tarifan sobre el precio de BLANCO
 *  con un 25 %% encima, NO sobre el de color. Con el blanco brillo del grupo 1
 *  en 18,40 €, un microarenado sale a 23,00 € y no a 26,54 €, que es lo que
 *  daría aplicárselo a la columna de color. */
export const ACB_LACA_COLORES = %s;""" % js({
    "estandar": COLORES_ESTANDAR,
    "especiales": COLORES_ESPECIALES,
    "decoraciones": [{"nombre": n, "pct": p} for n, p in DECORACIONES],
}))

out.append("""
/** COMPLEMENTOS por PIEZA (pág. 14): cornisas, portaluces, zócalo de 15,
 *  paneles, botelleros y campanas. Los precios van en el orden de
 *  `ACB_LACA_ACABADOS`. */
export const ACB_LACA_COMPLEMENTOS = %s;

/** Regletas y columnas de diseño (pág. 15). Estas SOLO se hacen en ultramatt,
 *  así que llevan dos precios y no cuatro: [blanco, color]. */
export const ACB_LACA_DISENO = %s;

/** Curvas para terminal (pág. 15), por alto. OJO: en las dos tablas CON
 *  MOLDURA la tarifa invierte brillo y ultramatt —el ultramatt cuesta más—, y
 *  lo hace en las nueve filas, así que no es un dígito suelto. */
export const ACB_LACA_CURVAS = %s;

/** Muebles y puertas RETRO (pág. 15). */
export const ACB_LACA_RETRO = %s;""" % (
    js([{"nombre": n, "precios": v} for n, v in COMPLEMENTOS]),
    js([{"nombre": n, "precios": v} for n, v in DISENO_ULTRAMATT]),
    js([{"grupo": g, "filas": [{"alto": n, "precios": v} for n, v in fs]}
        for g, fs in CURVAS]),
    js([{"nombre": n, "precios": v} for n, v in RETRO])))

out.append("""
/** COSTADOS (pág. 16), por SUPERFICIE en cm². Seis columnas, en el orden de
 *  `ACB_LACA_ACABADOS_COSTADO`. */
export const ACB_LACA_COSTADOS = %s;

/** Los recargos del costado, escritos donde se usan. */
export const ACB_LACA_COSTADO_22MM_PCT = %s;
export const ACB_LACA_COSTADO_30MM_PCT = %s;
export const ACB_LACA_COSTADO_ALIGERADO_PCT = %s;
export const ACB_LACA_COSTADO_ATAMBORADO_M2 = %s;

/** Y los del acabado (pág. 7). */
export const ACB_LACA_COLOR_ESPECIAL_PCT = %s;
export const ACB_LACA_XOLID_PCT = %s;
export const ACB_LACA_JUNQUILLOS_VITRINA = %s;
export const ACB_LACA_PANEL_MUESTRAS = %s;

/** «El precio para medidas especiales será igual al precio de la medida
 *  inmediata superior» (pág. 7). NO SE INTERPOLA nunca: se sube al escalón
 *  siguiente. Interpolar daría un precio que ACB no factura. */
export const ACB_LACA_MEDIDA_ESPECIAL = %s;""" % (
    js({"unaCara": [{"hasta": n, "precios": v} for n, v in COSTADOS_UNA_CARA],
        "dosCaras": [{"hasta": n, "precios": v} for n, v in COSTADOS_DOS_CARAS]}),
    COSTADO_22MM_PCT, COSTADO_30MM_PCT, COSTADO_ALIGERADO_PCT,
    COSTADO_ATAMBORADO_M2, COLOR_ESPECIAL_PCT, XOLID_PCT,
    JUNQUILLOS_VITRINA, PANEL_MUESTRAS, js(MEDIDA_ESPECIAL)))

out.append('''
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
    const tope = Number(String(t.hasta).match(/(\\d+)\\s*$/)[1]);
    if (s <= tope) return t;
  }
  return null;
};''')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    RAIZ, "frontend", "src", "data", "acbLaca.js")
with open(ruta, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("escrito", ruta)
