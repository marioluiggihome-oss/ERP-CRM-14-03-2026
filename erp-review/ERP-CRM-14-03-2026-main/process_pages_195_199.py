#!/usr/bin/env python3
"""
Process pages 195-199 from TARIFA-TECNICA-ZONACOCINAS
Pages 195-196: Title/Info pages (no products)
Pages 197-199: COLUMNAS DE 200cm FONDO 58cm
"""

import json
import re
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['test_database']

# Load existing valid references
with open('/app/valid_references.json', 'r') as f:
    valid_references = json.load(f)

initial_count = len(valid_references)
print(f"Referencias válidas iniciales: {initial_count}")

def extract_width(ref):
    match = re.search(r'(\d{3,4})$', ref)
    if match:
        w = int(match.group(1))
        return w / 10 if w >= 100 else w
    return 60.0

products_to_add = []

# ============================================
# PAGE 197 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD1P300", 238, 248, 267, 257, 279, 334, 359, 365, 386, 394, 408, 484),
    ("20CD1P350", 253, 263, 284, 277, 303, 341, 368, 374, 395, 412, 426, 501),
    ("20CD1P400", 268, 277, 300, 298, 327, 351, 377, 383, 404, 429, 444, 519),
    ("20CD1P450", 282, 292, 317, 319, 352, 375, 404, 412, 435, 447, 462, 536),
    ("20CD1P500", 297, 308, 336, 339, 376, 406, 440, 448, 475, 466, 480, 553),
    ("20CD1P600", 328, 339, 372, 382, 426, 432, 467, 476, 503, 504, 517, 590),
    ("20CD1P650", 380, 393, 431, 443, 495, 501, 542, 552, 583, 585, 599, 685),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 197, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD2P600", 392, 410, 448, 431, 475, 583, 634, 647, 688, 702, 732, 883),
    ("20CD2P700", 421, 440, 483, 470, 522, 599, 651, 664, 705, 739, 769, 919),
    ("20CD2P800", 452, 469, 516, 512, 570, 616, 670, 683, 725, 775, 804, 953),
    ("20CD2P900", 486, 505, 557, 560, 625, 672, 731, 744, 792, 817, 845, 993),
    ("20CD2P1000", 517, 539, 594, 602, 674, 735, 802, 818, 870, 854, 882, 1029),
    ("20CD2P1200", 576, 600, 664, 686, 773, 784, 855, 872, 927, 927, 954, 1100),
    ("20CD2P1300", 680, 707, 783, 809, 912, 926, 1009, 1028, 1094, 1094, 1126, 1298),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 197, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD1V300", 333, 311, 352, 353, 342, 393, 418, 424, 450, 458, 496, 571),
    ("20CD1V350", 348, 326, 369, 373, 366, 400, 426, 433, 459, 476, 513, 588),
    ("20CD1V400", 362, 340, 385, 394, 390, 410, 436, 442, 468, 494, 531, 606),
    ("20CD1V450", 377, 355, 402, 418, 415, 434, 463, 470, 499, 511, 549, 623),
    ("20CD1V500", 392, 371, 421, 442, 439, 465, 499, 507, 539, 530, 567, 641),
    ("20CD1V600", 422, 402, 457, 479, 489, 490, 526, 534, 567, 568, 604, 677),
    ("20CD1V650", 498, 475, 539, 565, 577, 579, 621, 631, 669, 670, 712, 799),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 197, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 198 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD2V600", 560, 530, 616, 620, 595, 700, 752, 764, 805, 820, 849, 1001),
    ("20CD2V700", 589, 561, 651, 659, 643, 716, 769, 781, 822, 857, 886, 1036),
    ("20CD2V800", 620, 590, 684, 701, 691, 734, 788, 800, 842, 893, 922, 1071),
    ("20CD2V900", 654, 626, 725, 749, 746, 790, 848, 862, 909, 935, 963, 1111),
    ("20CD2V1000", 685, 659, 762, 791, 795, 853, 920, 936, 988, 971, 1000, 1147),
    ("20CD2V1200", 744, 720, 832, 875, 894, 902, 972, 989, 1045, 1045, 1072, 1218),
    ("20CD2V1300", 878, 850, 981, 1032, 1054, 1064, 1147, 1167, 1233, 1233, 1265, 1437),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 198, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD1P1P300", 243, 253, 273, 266, 290, 359, 389, 396, 420, 416, 431, 513),
    ("20CD1P1P350", 258, 268, 290, 288, 315, 371, 402, 410, 434, 436, 455, 532),
    ("20CD1P1P400", 273, 284, 308, 310, 341, 379, 410, 417, 441, 455, 473, 550),
    ("20CD1P1P450", 288, 298, 324, 332, 368, 405, 439, 447, 475, 474, 487, 569),
    ("20CD1P1P500", 303, 315, 344, 354, 394, 439, 478, 486, 517, 494, 506, 588),
    ("20CD1P1P600", 335, 347, 380, 400, 447, 460, 499, 508, 540, 533, 546, 627),
    ("20CD1P1P650", 395, 409, 449, 472, 528, 543, 589, 600, 637, 629, 644, 740),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 198, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD2P2P600", 400, 420, 460, 446, 494, 633, 693, 708, 754, 747, 776, 942),
    ("20CD2P2P700", 432, 452, 497, 490, 546, 657, 719, 734, 782, 786, 824, 980),
    ("20CD2P2P800", 462, 482, 531, 536, 600, 673, 735, 750, 798, 825, 860, 1017),
    ("20CD2P2P900", 498, 518, 571, 586, 657, 732, 800, 817, 870, 869, 897, 1059),
    ("20CD2P2P1000", 529, 552, 610, 631, 710, 800, 877, 896, 956, 908, 935, 1097),
    ("20CD2P2P1200", 591, 614, 681, 720, 816, 840, 919, 938, 1000, 987, 1012, 1173),
    ("20CD2P2P1300", 698, 725, 804, 850, 963, 991, 1084, 1106, 1180, 1165, 1194, 1384),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 198, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 199 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 1 vitrina + 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD1V1V300", 366, 382, 412, 401, 438, 542, 587, 598, 634, 628, 650, 775),
    ("20CD1V1V350", 390, 404, 438, 434, 476, 560, 607, 618, 655, 658, 687, 804),
    ("20CD1V1V400", 412, 428, 465, 468, 515, 572, 618, 629, 666, 687, 713, 831),
    ("20CD1V1V450", 434, 450, 490, 501, 555, 612, 663, 675, 717, 715, 736, 859),
    ("20CD1V1V500", 458, 476, 520, 534, 595, 663, 721, 734, 780, 745, 764, 888),
    ("20CD1V1V600", 506, 523, 574, 604, 675, 694, 753, 767, 815, 805, 824, 947),
    ("20CD1V1V650", 597, 617, 677, 713, 797, 819, 889, 906, 962, 950, 973, 1117),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 vitrina + 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 199, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 vitrinas + 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CD2V2V600", 684, 718, 786, 763, 844, 1083, 1185, 1210, 1289, 1277, 1327, 1611),
    ("20CD2V2V700", 738, 772, 849, 838, 934, 1124, 1230, 1255, 1338, 1345, 1409, 1675),
    ("20CD2V2V800", 790, 824, 909, 916, 1025, 1151, 1257, 1282, 1365, 1411, 1471, 1740),
    ("20CD2V2V900", 851, 885, 977, 1002, 1124, 1251, 1368, 1397, 1488, 1487, 1533, 1812),
    ("20CD2V2V1000", 905, 944, 1043, 1079, 1214, 1368, 1499, 1532, 1634, 1553, 1598, 1876),
    ("20CD2V2V1200", 1011, 1050, 1165, 1232, 1395, 1436, 1571, 1603, 1709, 1688, 1731, 2006),
    ("20CD2V2V1300", 1193, 1239, 1375, 1453, 1646, 1695, 1854, 1892, 2017, 1992, 2042, 2367),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 vitrinas + 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 199, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CE1P300", 239, 249, 268, 258, 280, 335, 360, 366, 387, 395, 410, 485),
    ("20CE1P350", 254, 264, 285, 278, 305, 342, 369, 375, 396, 413, 427, 502),
    ("20CE1P400", 269, 278, 301, 299, 328, 352, 378, 384, 405, 431, 445, 520),
    ("20CE1P450", 284, 293, 318, 320, 353, 376, 405, 413, 436, 448, 463, 537),
    ("20CE1P500", 298, 309, 337, 340, 377, 407, 441, 449, 476, 467, 481, 554),
    ("20CE1P600", 329, 340, 373, 383, 427, 433, 468, 477, 504, 505, 518, 591),
    ("20CE1P650", 380, 393, 431, 443, 495, 501, 542, 552, 583, 585, 599, 685),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 199, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PROCESS ALL PRODUCTS
# ============================================

new_refs = []
updated_count = 0
created_count = 0

for product in products_to_add:
    ref = product["reference"]
    # Add required fields
    product["code"] = ref
    product["module"] = "montada"
    product["ancho"] = product["width"]
    product["alto"] = product["height"]
    product["fondo"] = product["depth"]
    product["points"] = product["zonePoints"]["Z1"]
    product["visualType"] = "columna"
    product["manufacturer"] = "Zona Cocinas"
    product["catalogId"] = "cat-m-base"
    
    if ref not in valid_references:
        valid_references.append(ref)
        new_refs.append(ref)
    
    existing = db.products.find_one({"reference": ref})
    if existing:
        db.products.update_one({"reference": ref}, {"$set": product})
        updated_count += 1
    else:
        db.products.insert_one(product)
        created_count += 1

with open('/app/valid_references.json', 'w') as f:
    json.dump(sorted(valid_references), f, indent=2)

print(f"\n{'='*50}")
print(f"RESUMEN - PÁGINAS 195-199")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
