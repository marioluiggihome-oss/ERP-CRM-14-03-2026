#!/usr/bin/env python3
"""
Process pages 220-224 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - COLUMNAS DE 220cm FONDO 58cm
"""

import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'kitchen_crm')]

# Load existing valid references
with open('/app/valid_references.json', 'r') as f:
    valid_references = json.load(f)

initial_count = len(valid_references)
print(f"Referencias válidas iniciales: {initial_count}")

products_to_add = []

# ============================================
# PAGE 220 - COLUMNAS DE 220cm FONDO 58cm
# ============================================

# Columna 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD1P300", 256, 266, 287, 278, 302, 372, 401, 408, 433, 426, 441, 524),
    ("22CD1P350", 272, 282, 306, 301, 330, 384, 415, 422, 447, 447, 466, 544),
    ("22CD1P400", 289, 299, 324, 324, 357, 393, 423, 432, 456, 467, 484, 563),
    ("22CD1P450", 305, 315, 343, 349, 384, 420, 455, 463, 490, 487, 501, 583),
    ("22CD1P500", 321, 333, 363, 372, 412, 455, 494, 503, 533, 507, 521, 602),
    ("22CD1P600", 356, 368, 402, 420, 468, 478, 518, 527, 559, 549, 562, 643),
    ("22CD1P650", 413, 426, 466, 487, 543, 554, 600, 611, 648, 637, 652, 745),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 220, "width": int(ref[-3:]) / 10, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD2P600", 420, 440, 482, 465, 513, 651, 711, 726, 773, 761, 791, 957),
    ("22CD2P700", 454, 475, 521, 512, 568, 677, 739, 754, 803, 802, 840, 996),
    ("22CD2P800", 486, 507, 559, 560, 624, 695, 757, 772, 821, 843, 878, 1035),
    ("22CD2P900", 525, 546, 601, 612, 685, 756, 824, 842, 896, 889, 917, 1079),
    ("22CD2P1000", 559, 582, 643, 659, 739, 825, 903, 922, 983, 930, 957, 1119),
    ("22CD2P1200", 625, 649, 719, 754, 851, 869, 948, 968, 1030, 1012, 1037, 1198),
    ("22CD2P1300", 737, 766, 849, 890, 1004, 1026, 1119, 1142, 1215, 1194, 1224, 1414),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 220, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD1V300", 351, 329, 371, 373, 365, 435, 464, 471, 496, 489, 504, 587),
    ("22CD1V350", 366, 345, 390, 396, 393, 447, 478, 485, 510, 510, 529, 607),
    ("22CD1V400", 383, 362, 408, 419, 420, 456, 486, 495, 519, 530, 547, 626),
    ("22CD1V450", 399, 378, 427, 443, 447, 483, 518, 526, 553, 550, 564, 646),
    ("22CD1V500", 416, 396, 447, 466, 475, 518, 557, 566, 596, 570, 584, 665),
    ("22CD1V600", 450, 431, 486, 515, 531, 541, 581, 590, 622, 612, 625, 706),
    ("22CD1V650", 532, 508, 574, 607, 627, 638, 685, 696, 733, 722, 737, 833),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 220, "width": int(ref[-3:]) / 10, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 221 - COLUMNAS DE 220cm FONDO 58cm (continuación)
# ============================================

# Columna 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD2V600", 609, 561, 651, 654, 634, 777, 832, 852, 899, 887, 917, 1083),
    ("22CD2V700", 643, 595, 690, 701, 689, 803, 860, 880, 929, 928, 966, 1122),
    ("22CD2V800", 675, 628, 728, 749, 744, 821, 878, 898, 947, 969, 1004, 1161),
    ("22CD2V900", 714, 667, 770, 801, 805, 882, 945, 968, 1022, 1015, 1043, 1205),
    ("22CD2V1000", 748, 702, 812, 848, 860, 951, 1024, 1048, 1109, 1056, 1083, 1245),
    ("22CD2V1200", 814, 770, 888, 943, 971, 995, 1069, 1094, 1156, 1138, 1163, 1324),
    ("22CD2V1300", 960, 908, 1048, 1113, 1146, 1175, 1261, 1291, 1364, 1343, 1373, 1562),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 221, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD1P1P300", 268, 279, 303, 290, 316, 383, 415, 422, 447, 466, 489, 596),
    ("22CD1P1P350", 286, 297, 324, 314, 345, 403, 437, 445, 473, 488, 522, 617),
    ("22CD1P1P400", 303, 315, 343, 338, 374, 416, 450, 459, 486, 511, 541, 639),
    ("22CD1P1P450", 320, 333, 364, 363, 403, 442, 480, 489, 519, 533, 557, 662),
    ("22CD1P1P500", 338, 352, 387, 389, 433, 469, 510, 521, 552, 557, 579, 684),
    ("22CD1P1P600", 375, 390, 429, 439, 492, 510, 554, 566, 601, 603, 625, 728),
    ("22CD1P1P650", 442, 460, 507, 518, 581, 602, 654, 668, 709, 711, 737, 859),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 221, "width": 30, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD2P2P600", 445, 467, 515, 488, 542, 675, 738, 754, 803, 840, 887, 1100),
    ("22CD2P2P700", 480, 504, 557, 538, 600, 716, 783, 800, 853, 886, 951, 1145),
    ("22CD2P2P800", 516, 539, 596, 586, 656, 741, 810, 827, 881, 932, 992, 1189),
    ("22CD2P2P900", 557, 581, 645, 642, 721, 799, 875, 894, 953, 983, 1027, 1237),
    ("22CD2P2P1000", 592, 620, 690, 692, 780, 855, 937, 957, 1021, 1029, 1073, 1282),
    ("22CD2P2P1200", 664, 692, 773, 793, 899, 935, 1024, 1046, 1116, 1120, 1163, 1370),
    ("22CD2P2P1300", 783, 817, 912, 935, 1061, 1103, 1208, 1234, 1317, 1322, 1373, 1617),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 221, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 222 - COLUMNAS DE 220cm FONDO 58cm (continuación)
# ============================================

# Columna 1 vitrina + 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD1V1V300", 432, 451, 486, 473, 516, 640, 692, 705, 748, 741, 767, 915),
    ("22CD1V1V350", 460, 477, 516, 513, 561, 660, 717, 730, 773, 776, 810, 949),
    ("22CD1V1V400", 486, 505, 548, 552, 608, 675, 730, 743, 786, 810, 842, 980),
    ("22CD1V1V450", 513, 531, 578, 591, 655, 722, 782, 797, 846, 844, 868, 0),
    ("22CD1V1V500", 541, 561, 614, 630, 702, 782, 851, 866, 920, 879, 902, 0),
    ("22CD1V1V600", 597, 617, 677, 713, 797, 819, 889, 906, 962, 950, 973, 1117),
    ("22CD1V1V650", 704, 729, 799, 841, 940, 967, 1049, 1069, 1135, 1121, 1148, 1318),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 vitrina + 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 222, "width": 30, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 vitrinas + 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CD2V2V600", 807, 847, 928, 900, 996, 1278, 1398, 1428, 1521, 1506, 1566, 1900),
    ("22CD2V2V700", 871, 911, 1002, 989, 1102, 1326, 1451, 1481, 1578, 1587, 1663, 1977),
    ("22CD2V2V800", 932, 972, 1072, 1081, 1210, 1358, 1483, 1513, 1610, 1665, 1735, 2053),
    ("22CD2V2V900", 1004, 1045, 1153, 1182, 1326, 1477, 1614, 1648, 1756, 1754, 1809, 2138),
    ("22CD2V2V1000", 1068, 1114, 1231, 1273, 1432, 1614, 1769, 1807, 1928, 1833, 1886, 2214),
    ("22CD2V2V1200", 1193, 1239, 1375, 1453, 1646, 1695, 1854, 1892, 2017, 1992, 2042, 2367),
    ("22CD2V2V1300", 1408, 1463, 1623, 1715, 1943, 2000, 2188, 2233, 2380, 2350, 2410, 2793),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 vitrinas + 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 222, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CE1P300", 256, 266, 287, 278, 302, 372, 401, 408, 433, 426, 441, 524),
    ("22CE1P350", 272, 282, 306, 301, 330, 384, 415, 422, 447, 447, 466, 544),
    ("22CE1P400", 289, 299, 324, 324, 357, 393, 423, 432, 456, 467, 484, 563),
    ("22CE1P450", 305, 315, 343, 349, 384, 420, 455, 463, 490, 487, 501, 583),
    ("22CE1P500", 321, 333, 363, 372, 412, 455, 494, 503, 533, 507, 521, 602),
    ("22CE1P600", 356, 368, 402, 420, 468, 478, 518, 527, 559, 549, 562, 643),
    ("22CE1P650", 413, 426, 466, 487, 543, 554, 600, 611, 648, 637, 652, 745),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 222, "width": 30, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 223 - COLUMNAS ESCOBERO DE 220cm
# ============================================

# Columna escobero 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CE2P600", 420, 440, 482, 465, 513, 651, 711, 726, 773, 761, 791, 957),
    ("22CE2P700", 454, 475, 521, 512, 568, 677, 739, 754, 803, 802, 840, 996),
    ("22CE2P800", 486, 507, 559, 560, 624, 695, 757, 772, 821, 843, 878, 1035),
    ("22CE2P900", 525, 546, 601, 612, 685, 756, 824, 842, 896, 889, 917, 1079),
    ("22CE2P1000", 620, 644, 709, 722, 808, 892, 973, 994, 1057, 1049, 1082, 1274),
    ("22CE2P1200", 731, 760, 836, 852, 953, 1053, 1148, 1173, 1247, 1238, 1276, 1503),
    ("22CE2P1300", 863, 897, 987, 1006, 1125, 1242, 1354, 1384, 1472, 1461, 1506, 1773),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 223, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CE1P1P300", 257, 267, 288, 279, 303, 373, 402, 410, 434, 427, 442, 525),
    ("22CE1P1P350", 273, 284, 307, 302, 331, 385, 416, 423, 448, 448, 467, 545),
    ("22CE1P1P400", 290, 300, 326, 326, 358, 394, 424, 433, 457, 468, 485, 564),
    ("22CE1P1P450", 306, 316, 344, 350, 385, 421, 456, 464, 491, 488, 502, 584),
    ("22CE1P1P500", 322, 334, 364, 373, 413, 456, 495, 504, 534, 508, 522, 603),
    ("22CE1P1P600", 357, 369, 403, 421, 469, 479, 519, 528, 560, 550, 563, 644),
    ("22CE1P1P650", 421, 435, 476, 497, 554, 565, 612, 623, 660, 649, 664, 760),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 223, "width": 30, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CE2P2P600", 422, 442, 484, 467, 516, 653, 713, 728, 775, 763, 793, 959),
    ("22CE2P2P700", 456, 477, 523, 515, 570, 679, 741, 756, 805, 804, 842, 999),
    ("22CE2P2P800", 488, 509, 561, 562, 626, 697, 759, 774, 823, 845, 880, 1037),
    ("22CE2P2P900", 527, 548, 603, 614, 687, 758, 826, 844, 898, 891, 919, 1082),
    ("22CE2P2P1000", 622, 647, 711, 725, 810, 895, 975, 996, 1059, 1052, 1084, 1276),
    ("22CE2P2P1200", 734, 763, 839, 855, 956, 1056, 1151, 1175, 1250, 1241, 1279, 1506),
    ("22CE2P2P1300", 866, 901, 990, 1009, 1128, 1246, 1358, 1387, 1475, 1465, 1510, 1777),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 223, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 224 - COLUMNAS FRIGO DE 220cm
# ============================================

# Columna Frigo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CF1P600", 356, 368, 402, 420, 468, 478, 518, 527, 559, 549, 562, 643),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna Frigo 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 224, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna Frigo 1 puerta (Derecha/Izquierda) + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CF1P1PABL600", 513, 525, 560, 578, 626, 635, 675, 685, 716, 707, 719, 800),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna Frigo 1 puerta (Derecha/Izquierda) + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 224, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna Frigo 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CF1P1P600", 369, 382, 421, 423, 473, 484, 524, 534, 566, 574, 596, 692),
    ("22CF1P1P750", 435, 451, 497, 499, 558, 571, 618, 631, 668, 678, 704, 817),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna Frigo 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 224, "width": 60, "height": 220, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Note: 22CF1P1P1PABL600 and 22CF1P1P1PABL750 have empty values, skipping

# ============================================
# PROCESS ALL PRODUCTS
# ============================================

created = 0
updated = 0
new_refs = []

for product in products_to_add:
    ref = product["reference"]
    
    # Add to valid references if not already present
    if ref not in valid_references:
        valid_references.append(ref)
        new_refs.append(ref)
    
    # Check if product exists
    existing = db.products.find_one({"reference": ref})
    
    if existing:
        # Update existing product
        db.products.update_one(
            {"reference": ref},
            {"$set": product}
        )
        updated += 1
    else:
        # Insert new product
        db.products.insert_one(product)
        created += 1

# Save updated valid references
with open('/app/valid_references.json', 'w') as f:
    json.dump(sorted(valid_references), f, indent=2)

# Final summary
final_count = len(valid_references)
total_products = db.products.count_documents({})

print(f"\n{'='*50}")
print(f"RESUMEN - PÁGINAS 220-224")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created}")
print(f"Productos actualizados: {updated}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
