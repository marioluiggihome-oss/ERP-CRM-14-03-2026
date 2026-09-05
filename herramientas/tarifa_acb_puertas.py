# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Genera frontend/src/data/acbPuertas.js desde la tarifa ACB PUERTAS 2026.

Transcrita del PDF «ACB PUERTAS TARIFA CANTEADO 2026», páginas 43 a 46.
Se escribe en tablas compactas y se VALIDA antes de emitir nada: los precios
tienen que subir con el ancho dentro de cada alto. Un dígito mal leído en una
tarifa no da ningún error — sale en un presupuesto.
"""
import json, sys

# ── FRENTES ─────────────────────────────────────────────────────────────────
# (altos, anchos, {serie: [precios en el mismo orden que los anchos]})
# `None` = la casilla del PDF pone «----», o sea que ESA MEDIDA NO SE FABRICA en
# esa serie. No es 0 €.
N = None
# Cada bloque: (altos, anchos, {(serie, canto): [precios]}).
# EL CANTO ES UNA DIMENSION MAS, no una serie aparte: las series Touch se
# tarifan en canto PVC y canto ALMA, y el ALMA cuesta siempre un poco mas. Las
# demas solo llevan PVC (o «PVC ó TEC-LINE», que es un unico precio).
FRENTES = [
    # ── pág. 43: SERIE GM 2.0 y SERIE QUALITA ──────────────────────────────
    ([558], [248,298,348,398,448,498,598], {
        ('gm20','pvc'):    [19.81,19.81,22.09,24.22,26.45,28.93,33.40],
        ('qualita','pvc'): [26.09,26.09,29.19,32.08,35.14,38.48,44.56]}),
    ([598], [598], {('gm20','pvc'):[37.48], ('qualita','pvc'):[50.10]}),
    ([698], [248,298,348,398,448,498,598], {
        ('gm20','pvc'):    [22.33,22.33,24.87,26.99,29.75,32.55,37.48],
        ('qualita','pvc'): [29.47,29.47,32.94,35.85,39.58,43.37,50.09]}),
    ([798], [248,298,348,398,448,498,598], {
        ('gm20','pvc'):    [25.42,25.42,28.22,30.85,33.73,36.99,42.44],
        ('qualita','pvc'): [33.68,33.68,37.54,41.27,45.06,49.47,56.98]}),
    ([898], [248,298,348,398,448,498,598], {
        ('gm20','pvc'):    [27.63,27.63,30.67,33.54,36.66,40.21,46.13],
        ('qualita','pvc'): [36.63,36.63,40.78,44.96,48.96,53.74,61.92]}),
    ([1198,1298], [298,348,398,448,498,598], {
        ('gm20','pvc'):    [38.25,42.40,46.48,50.53,55.34,63.63],
        ('qualita','pvc'): [50.81,56.51,62.15,67.77,74.31,85.67]}),
    ([1498,1598], [298,348,398,448,498,598], {
        ('gm20','pvc'):    [49.96,55.54,60.52,66.41,72.76,83.62],
        ('qualita','pvc'): [66.13,73.76,80.76,88.60,97.14,112.07]}),

    # ── págs. 45-46: LISOS · GALDAR · CALABRIA 8 · AURA ────────────────────
    ([138,173], [248,298,348,398,448,498,598,698,798,898,998,1198], {
        ('lisos','pvc'):     [9.71,9.71,10.67,11.62,12.56,13.52,15.43,18.52,21.60,23.15,27.04,30.86],
        ('galdar','pvc'):    [14.39,14.39,15.80,17.17,17.88,18.59,19.43,23.31,27.20,29.14,37.19,38.85],
        ('calabria8','pvc'): [N]*12, ('auraResto','pvc'): [N]*12, ('auraSense','pvc'): [N]*12}),
    ([278], [298,348,398,448,498,598,698,798,898,998,1198], {
        ('lisos','pvc'):     [10.62,11.75,12.88,14.02,15.14,17.39,19.67,21.91,24.17,30.27,34.79],
        ('galdar','pvc'):    [25.27,25.80,26.46,27.61,28.34,31.61,34.77,38.26,39.78,56.68,63.22],
        ('calabria8','pvc'): [18.49,20.44,22.41,24.39,26.34,30.26,34.21,38.14,42.06,52.67,60.52],
        ('auraResto','pvc'): [18.49,20.44,22.41,24.39,26.34,30.26,34.21,38.14,42.06,52.67,60.52],
        ('auraSense','pvc'): [27.73,30.65,33.62,36.58,39.51,45.39,51.32,57.21,63.10,79.01,90.79]}),
    ([348], [298,348,398,448,498,598,698,798,898], {
        ('lisos','pvc'):     [12.29,13.64,15.00,16.35,17.71,20.40,23.09,25.80,28.50],
        ('galdar','pvc'):    [26.15,27.09,28.12,29.18,30.20,33.21,36.54,40.19,41.76],
        ('calabria8','pvc'): [21.38,23.74,26.09,28.45,30.80,35.49,40.20,44.91,49.59],
        ('auraResto','pvc'): [21.38,23.74,26.09,28.45,30.80,35.49,40.20,44.91,49.59],
        ('auraSense','pvc'): [32.08,35.61,39.14,42.67,46.20,53.23,60.29,67.36,74.38]}),
    ([418], [298,598], {
        ('lisos','pvc'):[14.02,23.48], ('galdar','pvc'):[27.04,34.82], ('calabria8','pvc'):[24.39,40.85],
        ('auraResto','pvc'):[24.39,40.85], ('auraSense','pvc'):[36.58,61.27]}),
    ([448], [298,348,398,448,498,598,698,798,898], {
        ('lisos','pvc'):     [15.92,17.78,19.62,21.49,23.32,27.03,30.22,33.35,36.53],
        ('galdar','pvc'):    [29.08,30.55,32.04,34.71,36.66,39.61,51.94,54.46,59.00],
        ('calabria8','pvc'): [27.69,30.93,34.14,37.38,40.59,47.04,52.58,58.04,63.54],
        ('auraResto','pvc'): [27.69,30.93,34.14,37.38,40.59,47.04,52.58,58.04,63.54],
        ('auraSense','pvc'): [41.54,46.39,51.21,56.07,60.89,70.56,78.87,87.06,95.32]}),
    ([558], [248,298,348,398,448,498,598], {
        ('lisos','pvc'):     [17.31,17.31,19.32,21.32,23.35,25.35,29.38],
        ('galdar','pvc'):    [31.61,31.61,33.21,34.82,37.72,39.84,43.06],
        ('calabria8','pvc'): [30.10,30.10,33.62,37.11,40.63,44.12,51.13],
        ('auraResto','pvc'): [30.10,30.10,33.62,37.11,40.63,44.12,51.13],
        ('auraSense','pvc'): [45.15,45.15,50.43,55.67,60.94,66.18,76.70]}),
    ([598], [598], {
        ('lisos','pvc'):[35.40], ('galdar','pvc'):[46.62], ('calabria8','pvc'):[61.58],
        ('auraResto','pvc'):[61.58], ('auraSense','pvc'):[92.37]}),
    ([698], [248,298,348,398,448,498,598], {
        ('lisos','pvc'):     [20.64,20.64,23.09,25.56,28.01,30.48,35.40],
        ('galdar','pvc'):    [32.30,32.30,34.41,36.42,39.32,41.60,46.62],
        ('calabria8','pvc'): [35.92,35.92,40.20,44.47,48.75,53.03,61.58],
        ('auraResto','pvc'): [35.92,35.92,40.20,44.47,48.75,53.03,61.58],
        ('auraSense','pvc'): [53.88,53.88,60.29,66.71,73.12,79.54,92.37]}),
    ([798], [248,298,348,398,448,498,598], {
        ('lisos','pvc'):     [23.39,23.39,26.22,29.06,31.91,34.75,40.45],
        ('galdar','pvc'):    [35.76,35.76,37.68,39.65,42.89,45.72,49.35],
        ('calabria8','pvc'): [40.69,40.69,45.62,50.58,55.53,60.46,70.37],
        ('auraResto','pvc'): [40.69,40.69,45.62,50.58,55.53,60.46,70.37],
        ('auraSense','pvc'): [61.04,61.04,68.43,75.87,83.30,90.69,105.56]}),
    ([898], [248,298,348,398,448,498,598], {
        ('lisos','pvc'):     [25.42,25.42,28.50,31.59,34.68,37.78,43.96],
        ('galdar','pvc'):    [38.87,38.87,40.96,43.09,46.62,49.70,53.64],
        ('calabria8','pvc'): [44.23,44.23,49.59,54.97,60.36,65.72,76.49],
        ('auraResto','pvc'): [44.23,44.23,49.59,54.97,60.36,65.72,76.49],
        ('auraSense','pvc'): [66.34,66.34,74.38,82.46,90.54,98.58,114.74]}),
    ([1198,1298], [298,348,398,448,498,598], {
        ('lisos','pvc'):     [35.00,39.36,43.74,48.08,52.45,61.16],
        ('galdar','pvc'):    [53.64,56.93,60.19,65.13,70.06,76.30],
        ('calabria8','pvc'): [60.90,68.48,76.09,83.67,91.27,106.43],
        ('auraResto','pvc'): [60.90,68.48,76.09,83.67,91.27,106.43],
        ('auraSense','pvc'): [91.35,102.72,114.13,125.50,136.91,159.65]}),
    ([1498,1598], [298,348,398,448,498,598], {
        ('lisos','pvc'):     [46.07,51.59,57.15,62.69,68.26,79.36],
        ('galdar','pvc'):    [71.17,75.36,79.52,85.94,91.30,100.26],
        ('calabria8','pvc'): [80.15,89.78,99.45,109.11,118.75,138.07],
        ('auraResto','pvc'): [80.15,89.78,99.45,109.11,118.75,138.07],
        ('auraSense','pvc'): [120.22,134.68,149.17,163.67,178.12,207.11]}),
    # ── págs. 48-49: TOUCH 22MM · PALMA TOUCH 22MM · TOUCH 19MM ────────────
    # Estas tres se tarifan en DOS cantos: PVC y ALMA.
    ([138,173], [248,298,348,398,448,498,598,698,798,898,998,1198], {
        ('touch22','pvc'):   [9.21,9.21,10.49,11.68,12.81,14.09,16.45,20.97,23.36,25.63,28.17,32.91],
        ('touch22','alma'):  [9.54,9.54,10.85,12.09,13.26,14.58,17.03,21.71,24.18,26.53,29.16,34.06],
        ('palmaTouch','pvc'):[22.38,22.38,24.42,27.28,30.04,31.36,36.77,42.21,46.74,50.33,55.04,63.36],
        ('palmaTouch','alma'):[22.83,22.83,24.91,27.83,30.64,31.99,37.50,43.05,47.68,51.33,56.14,64.62],
        ('touch19','pvc'):   [8.29,8.29,9.44,10.51,11.53,12.68,14.81,18.88,21.02,23.07,25.35,29.62],
        ('touch19','alma'):  [8.58,8.58,9.77,10.88,11.94,13.12,15.33,19.54,21.76,23.87,26.24,30.65]}),
    ([278], [298,348,398,448,498,598,698,798,898,998,1198], {
        ('touch22','pvc'):   [13.71,15.30,16.94,18.59,20.33,23.69,26.76,30.09,33.22,40.65,47.38],
        ('touch22','alma'):  [14.19,15.83,17.54,19.24,21.04,24.52,27.70,31.14,34.38,42.08,49.04],
        ('palmaTouch','pvc'):[26.00,29.64,31.84,34.62,37.69,42.90,50.04,53.69,61.94,64.34,75.15],
        ('palmaTouch','alma'):[26.52,30.24,32.48,35.31,38.44,43.76,51.04,54.76,63.18,65.62,76.65],
        ('touch19','pvc'):   [12.34,13.77,15.25,16.73,18.29,21.32,24.09,27.08,29.90,36.59,42.65],
        ('touch19','alma'):  [12.77,14.25,15.78,17.31,18.93,22.07,24.93,28.03,30.94,37.87,44.14]}),
    ([348], [298,348,398,448,498,598,698,798,898], {
        ('touch22','pvc'):   [15.22,17.06,18.80,20.54,22.60,26.27,29.89,33.57,37.01],
        ('touch22','alma'):  [15.75,17.66,19.46,21.26,23.39,27.19,30.94,34.75,38.31],
        ('palmaTouch','pvc'):[26.87,30.65,35.02,36.12,39.00,45.02,51.40,54.57,63.09],
        ('palmaTouch','alma'):[27.41,31.27,35.72,36.84,39.78,45.92,52.42,55.67,64.35],
        ('touch19','pvc'):   [13.70,15.35,16.92,18.49,20.34,23.65,26.90,30.21,33.31],
        ('touch19','alma'):  [14.18,15.89,17.51,19.13,21.05,24.47,27.85,31.27,34.48]}),
    ([418], [298,598], {
        ('touch22','pvc'):[16.94,31.87], ('touch22','alma'):[17.54,32.98],
        ('palmaTouch','pvc'):[27.46,47.07], ('palmaTouch','alma'):[28.01,48.01],
        ('touch19','pvc'):[15.25,28.68], ('touch19','alma'):[15.78,29.69]}),
    ([448], [298,348,398,448,498,598,698,798,898], {
        ('touch22','pvc'):   [21.80,24.39,26.79,29.31,32.11,37.19,48.78,53.60,58.63],
        ('touch22','alma'):  [22.57,25.24,27.73,30.34,33.24,38.49,50.48,55.48,60.69],
        ('palmaTouch','pvc'):[28.41,32.67,34.81,39.45,43.02,51.40,59.42,66.44,72.11],
        ('palmaTouch','alma'):[28.98,33.33,35.51,40.24,43.88,52.42,60.61,67.77,73.55],
        ('touch19','pvc'):   [19.62,21.95,24.11,26.38,28.90,33.47,43.90,48.24,52.77],
        ('touch19','alma'):  [20.31,22.72,24.96,27.30,29.91,34.64,45.44,49.93,54.62]}),
    ([558], [248,298,348,398,448,498,598], {
        ('touch22','pvc'):   [23.69,23.69,26.51,29.13,31.87,34.90,40.42],
        ('touch22','alma'):  [24.52,24.52,27.44,30.15,32.98,36.12,41.83],
        ('palmaTouch','pvc'):[30.68,30.68,35.99,37.63,41.20,44.57,53.70],
        ('palmaTouch','alma'):[31.30,31.30,36.71,38.38,42.02,45.46,54.77],
        ('touch19','pvc'):   [21.32,21.32,23.86,26.22,28.68,31.41,36.38],
        ('touch19','alma'):  [22.07,22.07,24.69,27.14,29.69,32.51,37.65]}),
    ([598], [598], {
        ('touch22','pvc'):[45.44], ('touch22','alma'):[47.04],
        ('palmaTouch','pvc'):[55.09], ('palmaTouch','alma'):[56.19],
        ('touch19','pvc'):[40.90], ('touch19','alma'):[42.33]}),
    ([698], [248,298,348,398,448,498,598], {
        ('touch22','pvc'):   [26.76,26.76,29.89,32.52,35.92,39.34,45.45],
        ('touch22','alma'):  [27.70,27.70,30.94,33.65,37.18,40.72,47.04],
        ('palmaTouch','pvc'):[32.31,36.36,40.84,45.22,49.54,54.39,62.14],
        ('palmaTouch','alma'):[32.96,37.09,41.65,46.12,50.53,55.48,63.38],
        ('touch19','pvc'):   [24.09,24.09,26.90,29.26,32.33,35.41,40.90],
        ('touch19','alma'):  [24.93,24.93,27.85,30.29,33.46,36.65,42.33]}),
    ([798], [248,298,348,398,448,498,598], {
        ('touch22','pvc'):   [30.57,30.56,34.05,37.46,40.88,44.85,51.67],
        ('touch22','alma'):  [31.64,31.63,35.25,38.77,42.31,46.42,53.48],
        ('palmaTouch','pvc'):[35.13,37.84,42.00,46.38,50.52,55.90,64.00],
        ('palmaTouch','alma'):[35.83,38.60,42.84,47.31,51.53,57.02,65.28],
        ('touch19','pvc'):   [27.51,27.51,30.65,33.71,36.79,40.37,46.51],
        ('touch19','alma'):  [28.47,28.47,31.72,34.89,38.08,41.78,48.13]}),
    ([898], [248,298,348,398,448,498,598], {
        ('touch22','pvc'):   [33.23,33.22,37.01,40.71,44.43,48.75,56.17],
        ('touch22','alma'):  [34.39,34.38,38.31,42.14,45.98,50.46,58.13],
        ('palmaTouch','pvc'):[37.46,39.66,44.90,49.90,54.44,59.59,70.83],
        ('palmaTouch','alma'):[38.21,40.45,45.80,50.90,55.53,60.78,72.24],
        ('touch19','pvc'):   [29.90,29.90,33.31,36.64,39.99,43.88,50.55],
        ('touch19','alma'):  [30.95,30.94,34.48,37.92,41.39,45.41,52.32]}),
    # El 1180 es SOLO de Palma Touch; Touch 22 y 19 no lo fabrican.
    ([1180], [298,348,398,448,498,598], {
        ('palmaTouch','pvc'):[65.15,74.68,84.16,93.83,102.61,117.70],
        ('palmaTouch','alma'):[66.45,76.18,85.84,95.71,104.66,120.06]}),
    # Y el 1198 al reves: Touch 22 y 19 si, Palma Touch no.
    ([1198], [298,348,398,448,498,598], {
        ('touch22','pvc'):   [46.07,51.26,56.38,61.45,67.40,77.69],
        ('touch22','alma'):  [47.69,53.05,58.36,63.60,69.76,80.41],
        ('touch19','pvc'):   [41.47,46.13,50.74,55.31,60.66,69.92],
        ('touch19','alma'):  [42.92,47.75,52.52,57.24,62.78,72.37]}),
    ([1298], [298,348,398,448,498,598], {
        ('touch22','pvc'):   [46.07,51.26,56.38,61.45,67.40,77.69],
        ('touch22','alma'):  [47.69,53.05,58.36,63.60,69.76,80.41],
        ('palmaTouch','pvc'):[77.02,81.25,85.08,98.55,104.67,124.42],
        ('palmaTouch','alma'):[78.56,82.87,86.78,100.52,106.77,126.91],
        ('touch19','pvc'):   [41.47,46.13,50.74,55.31,60.66,69.92],
        ('touch19','alma'):  [42.92,47.75,52.52,57.24,62.78,72.37]}),
    # El 1298 x 698 solo lo hace Palma Touch.
    ([1298], [698], {
        ('palmaTouch','pvc'):[132.29], ('palmaTouch','alma'):[134.93]}),
]

# ── COMPLEMENTOS (pág. 44): se tarifan por SUPERFICIE, en cm² ───────────────
# El PDF dice «HASTA 500», «HASTA 1000»... en cm². Tres cantos posibles.
COMPLEMENTOS_TRAMOS = [500,1000,1500,2000,2500,3000,3500,4000,4500,5000,
                       5500,6000,6500,7000,7500,8000,8500,9000,9500,10000]
COMPLEMENTOS = {
    'gm20': {
        'unLargo':      [7.85,10.86,14.30,18.75,21.81,24.93,28.03,31.18,35.57,39.54,
                         41.60,45.73,49.04,51.49,54.44,56.23,61.46,64.71,68.34,76.70],
        'unLargoDosCortos':[8.18,13.20,16.17,21.21,23.62,25.64,30.92,35.60,38.20,40.32,
                         43.83,48.00,52.58,56.63,60.45,69.12,73.44,77.75,79.44,83.62],
        'cuatroCantos': [8.88,13.90,17.02,22.32,24.87,26.99,32.54,37.48,40.21,42.44,
                         46.14,50.53,55.34,59.61,63.63,72.76,77.30,81.84,83.62,88.02]},
    'qualita': {
        'unLargo':      [8.86,14.22,21.34,27.40,30.56,33.14,39.57,44.89,50.72,54.27,
                         58.07,62.14,66.48,71.14,76.12,81.45,87.15,95.52,99.78,106.76],
        'unLargoDosCortos':[9.69,17.30,21.37,28.14,31.43,34.18,41.37,47.79,51.26,54.33,
                         59.05,64.62,70.86,76.32,81.68,92.63,98.42,104.21,106.84,112.46],
        'cuatroCantos': [10.20,18.21,22.50,29.63,33.09,35.99,43.55,50.30,53.96,57.19,
                         62.17,68.02,74.60,80.33,85.98,97.51,103.59,109.69,112.47,118.38]},
    'lisosGaldarCalabriaAura': {
        'unLargo':      [9.15,11.46,13.23,15.02,19.96,22.08,26.33,29.57,32.64,35.89,
                         39.18,42.86,45.31,48.91,52.44,54.67,58.77,62.36,66.67,70.34],
        'unLargoDosCortos':[10.13,14.66,16.52,18.69,21.94,24.28,28.95,33.63,35.89,38.43,
                         41.77,45.67,49.82,53.66,58.10,64.85,68.89,72.94,75.24,79.35],
        'cuatroCantos': [10.66,15.43,17.39,19.67,23.09,25.56,30.48,35.40,37.78,40.45,
                         43.97,48.08,52.45,56.48,61.16,68.26,72.52,76.78,79.20,83.53]},
}
COSTADO_2440X600 = {
    'gm20':    {'unLargo':97.92, 'unLargoDosCortos':122.42, 'cuatroCantos':128.86},
    'qualita': {'unLargo':140.97,'unLargoDosCortos':164.64, 'cuatroCantos':173.31},
}
REGLETAS = [
    (698, 98, {'gm20':9.72,  'qualita':13.77}),
    (898, 98, {'gm20':13.90, 'qualita':16.65}),
    (2440,98, {'gm20':30.87, 'qualita':36.46}),
]

SERIES = [
    ('gm20','GM 2.0','Seda · Brillo','PVC ó TEC-LINE',
     'BERNA GM: hay que añadir aparte el precio del tirador GOLA.'),
    ('qualita','Qualita','Seda (antihuella)','PVC ó TEC-LINE',''),
    ('lisos','Lisos','Naturmel 19 · Natur+ Super Mate 22 · Slate 22 · Slate Sedalac 22 · Slate 0,0 22 · Aura 22','PVC',
     'BERNA: hay que añadir aparte el precio del tirador GOLA.'),
    ('galdar','Galdar','Naturmel 19MM · Slate 22MM','PVC',
     'Los modelos montados NO pueden llevar tirador gola.'),
    ('calabria8','Calabria 8','Slate: Nieve 0021 · Salvia 1423 · Cosmos 1049 · Blanco Nórdico · Robles 4677/4678/4675/4701/4569 · Nogales Samburu/Turkana/Tuareg','PVC',
     'Los frentes de alto/ancho menor de 238 son LISOS.'),
    ('auraResto','Aura · resto de plafones','Atlas · Mira · Lyra · Altair · Europa · Vesta — Roble Nébula · Nogal Eclipse · Fresno Nova','PVC',
     'Los frentes de alto/ancho menor de 238 son LISOS.'),
    ('auraSense','Aura · plafón Sense','Yute · Apolo','PVC',
     'Los frentes de alto/ancho menor de 238 son LISOS.'),
    ('touch22','Touch 22MM','Seda · Alto Brillo','PVC ó ALMA',
     'BERNA TOUCH: hay que añadir aparte el precio del tirador GOLA.'),
    ('palmaTouch','Palma Touch 22MM','Seda · Alto Brillo','PVC ó ALMA',
     'BERNA TOUCH: hay que añadir aparte el precio del tirador GOLA.'),
    ('touch19','Touch 19MM','Solo en Blanco Seda','PVC ó ALMA',
     'BERNA TOUCH: hay que añadir aparte el precio del tirador GOLA.'),
]

# Los cantos que existen, con su rótulo. El ALMA solo lo tienen las Touch.
CANTOS = [('pvc','Canto PVC'), ('alma','Canto ALMA')]

# ── VALIDACIÓN: dentro de un alto, el precio SUBE con el ancho ──────────────
fallos = []
for altos, anchos, series in FRENTES:
    for (sid, canto), precios in series.items():
        assert len(precios) == len(anchos), (altos, sid, canto, len(precios), len(anchos))
        prev = None
        for ancho, precio in zip(anchos, precios):
            if precio is None:
                continue
            # UN CENTIMO DE TOLERANCIA: la propia tarifa de ACB tiene
            # inversiones de un centimo por redondeo (el Touch 22 de 798x248
            # vale 30,57 y el de 798x298 vale 30,56). Lo que esto caza son
            # digitos mal leidos, y esos fallan por decenas, no por centimos.
            if prev is not None and prev - precio > 0.011:
                fallos.append(f"{sid}/{canto} alto {altos} ancho {ancho}: {precio} < {prev}")
            prev = precio
for sid, cantos in COMPLEMENTOS.items():
    for canto, vals in cantos.items():
        assert len(vals) == len(COMPLEMENTOS_TRAMOS), (sid, canto)
        for a, b in zip(vals, vals[1:]):
            if b < a:
                fallos.append(f"complementos {sid}/{canto}: {b} < {a}")
if fallos:
    print("REVISAR (el precio baja al crecer la pieza):")
    for f in fallos: print("  ", f)
else:
    print("✓ validado: en todas las series el precio sube con el ancho")
print(f"  series: {len(SERIES)} · bloques de frentes: {len(FRENTES)}")
n = sum(len([p for p in v if p is not None]) for _,_,s in FRENTES for v in s.values())
print(f"  precios de frente transcritos: {n}")

# ── EMITIR EL FICHERO ───────────────────────────────────────────────────────
filas = []
for altos, anchos, series in FRENTES:
    for (sid, canto), precios in series.items():
        for ancho, precio in zip(anchos, precios):
            if precio is None:
                continue
            filas.append({"serie": sid, "canto": canto, "altos": altos,
                          "ancho": ancho, "precio": precio})
filas.sort(key=lambda f: (f["serie"], f["canto"], f["altos"][0], f["ancho"]))

def js(o):
    return json.dumps(o, ensure_ascii=False)

out = ['''/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// TARIFA DE PUERTAS Y FRENTES DEL GRUPO ACB (Canteado Industrial S.L.), 2026.
//
// Transcrita del PDF oficial «ACB PUERTAS TARIFA CANTEADO 2026». Es el hermano
// de `cascos.js`: allí están los cuerpos de mueble y aquí los frentes, del
// mismo proveedor. Se genera con `herramientas/tarifa_acb_puertas.py`, que
// VALIDA los números antes de escribir nada — dentro de cada alto el precio
// tiene que subir con el ancho. Un dígito mal leído en una tarifa no da ningún
// error: sale en un presupuesto y se ve cuando llega la factura.
//
// LO QUE NO SE FABRICA NO ESTÁ. Las casillas que el PDF deja en «----» no se
// escriben como 0 €: se omiten. Un cero ahí sería un frente gratis en el
// escandallo (CLAUDE.md, regla 7).
//
// PRECIOS DE TARIFA, ANTES DE DESCUENTO. El descuento de ACB lo teclea el
// master, porque se negocia y cambia (igual que en los cascos).

/** Las series del catálogo, con lo que hay que saber al pedirlas. */
export const ACB_PUERTAS_SERIES = [''']
for sid, label, acabados, canto, nota in SERIES:
    cantos = sorted({c for _, _, ss in FRENTES for (s2, c) in ss if s2 == sid})
    out.append("  { id: %s, label: %s, acabados: %s, canto: %s, cantos: %s, nota: %s }," % (
        js(sid), js(label), js(acabados), js(canto), js(cantos), js(nota)))
out.append("];\n")

out.append("""/** Los altos y anchos que ACB fabrica, en MILÍMETROS.
 *  Un alto como «1198 & 1298» son DOS medidas al mismo precio: por eso `altos`
 *  es una lista y no un número. */""")
out.append("export const ACB_PUERTAS = [")
for f in filas:
    out.append("  { serie: %s, canto: %s, altos: %s, ancho: %d, precio: %s }," % (
        js(f["serie"]), js(f["canto"]), js(f["altos"]), f["ancho"], f["precio"]))
out.append("];\n")

out.append("""/** COMPLEMENTOS: costados, zócalos y piezas sueltas. No van por medida
 *  concreta sino por SUPERFICIE en cm², y el precio depende de cuántos cantos
 *  lleve la pieza. Solo GM 2.0 y Qualita los tarifan así. */""")
out.append("export const ACB_COMPLEMENTOS_TRAMOS = %s;" % js(COMPLEMENTOS_TRAMOS))
out.append("export const ACB_CANTOS = %s;" % js([{"id": c, "label": l} for c, l in CANTOS]))
out.append("export const ACB_COMPLEMENTOS_CANTOS = [")
out.append("  { id: 'unLargo', label: '1 largo' },")
out.append("  { id: 'unLargoDosCortos', label: '1 largo + 2 cortos' },")
out.append("  { id: 'cuatroCantos', label: '4 cantos' },")
out.append("];")
out.append("export const ACB_COMPLEMENTOS = %s;\n" % js(COMPLEMENTOS))
out.append("/** El costado entero de 2440 x 600, que va aparte de los tramos. */")
out.append("export const ACB_COSTADO_2440X600 = %s;\n" % js(COSTADO_2440X600))
out.append("""/** Regletas, a medida fija. */
export const ACB_REGLETAS = [""")
for alto, ancho, precios in REGLETAS:
    out.append("  { alto: %d, ancho: %d, precios: %s }," % (alto, ancho, js(precios)))
out.append("];\n")

out.append('''/** EL ZÓCALO SIN CANTEAR TIENE SU PROPIA REGLA (pág. 44 del PDF):
 *  «se hace un descuento del 10 % sobre el precio del costado a 1 largo».
 *  Va aquí y no escrito a mano en la pantalla, para que no acabe habiendo dos
 *  descuentos distintos para lo mismo. */
export const ACB_ZOCALO_SIN_CANTEAR_DTO = 0.10;

/** Busca el precio de un frente. Devuelve `null` cuando ACB NO fabrica esa
 *  medida en esa serie y ese canto — que es distinto de que valga cero.
 *
 *  EL CANTO ENTRA EN LA BUSQUEDA, no se coge el primero que aparezca: en las
 *  series Touch, el canto ALMA cuesta siempre mas que el PVC, y devolver
 *  cualquiera de los dos seria un precio equivocado sin dar ningun error. */
export const precioFrenteACB = (serie, canto, alto, ancho) => {
  const a = Number(alto), w = Number(ancho);
  if (!Number.isFinite(a) || !Number.isFinite(w)) return null;
  const f = ACB_PUERTAS.find(
    (x) => x.serie === serie && x.canto === canto
        && x.altos.includes(a) && x.ancho === w);
  return f ? f.precio : null;
};

/** Los cantos que ACB fabrica de verdad en esta serie. */
export const cantosDeSerieACB = (serie) => {
  const s = ACB_PUERTAS_SERIES.find((x) => x.id === serie);
  const ids = (s && s.cantos) || ['pvc'];
  return ACB_CANTOS.filter((c) => ids.includes(c.id));
};''')

ruta = "frontend/src/data/acbPuertas.js"
import os
os.chdir("/home/user/ERP-CRM-14-03-2026")
with open(ruta, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("escrito", ruta, len(filas), "filas de frente")
