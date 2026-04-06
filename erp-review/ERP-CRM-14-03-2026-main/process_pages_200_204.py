#!/usr/bin/env python3
"""
Process pages 200-204 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - COLUMNAS DE 200cm FONDO 58cm (continuación)
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
# PAGE 200 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna escobero 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CE2P600", 392, 410, 448, 431, 475, 583, 634, 647, 688, 702, 732, 883),
    ("20CE2P700", 421, 440, 483, 470, 522, 599, 651, 664, 705, 739, 769, 919),
    ("20CE2P800", 452, 469, 516, 512, 570, 616, 670, 683, 725, 775, 804, 953),
    ("20CE2P900", 486, 505, 557, 560, 625, 672, 731, 744, 792, 817, 845, 993),
    ("20CE2P1000", 517, 539, 594, 602, 674, 735, 802, 818, 870, 854, 882, 1029),
    ("20CE2P1200", 576, 600, 664, 686, 773, 784, 855, 872, 927, 927, 954, 1100),
    ("20CE2P1300", 680, 707, 783, 809, 912, 926, 1009, 1028, 1094, 1094, 1126, 1298),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 200, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CE1P1P300", 239, 249, 268, 258, 280, 335, 360, 366, 387, 395, 410, 485),
    ("20CE1P1P350", 254, 264, 285, 278, 305, 342, 369, 375, 396, 413, 427, 502),
    ("20CE1P1P400", 269, 278, 301, 299, 328, 352, 378, 384, 405, 431, 445, 520),
    ("20CE1P1P450", 284, 293, 318, 320, 353, 376, 405, 413, 436, 448, 463, 537),
    ("20CE1P1P500", 298, 309, 337, 340, 377, 407, 441, 449, 476, 467, 481, 554),
    ("20CE1P1P600", 329, 340, 373, 383, 427, 433, 468, 477, 504, 505, 518, 591),
    ("20CE1P1P650", 380, 394, 432, 443, 495, 501, 542, 551, 584, 585, 600, 685),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 200, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna escobero 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CE2P2P600", 394, 412, 450, 433, 477, 585, 636, 649, 690, 705, 734, 885),
    ("20CE2P2P700", 423, 442, 485, 472, 524, 601, 653, 666, 707, 741, 771, 921),
    ("20CE2P2P800", 454, 471, 518, 514, 572, 618, 672, 685, 727, 777, 806, 956),
    ("20CE2P2P900", 488, 507, 559, 562, 627, 674, 733, 746, 794, 819, 847, 995),
    ("20CE2P2P1000", 516, 539, 596, 617, 696, 786, 863, 882, 942, 895, 921, 1084),
    ("20CE2P2P1200", 578, 601, 668, 707, 802, 826, 905, 924, 986, 973, 999, 1159),
    ("20CE2P2P1300", 684, 711, 790, 836, 949, 977, 1070, 1092, 1166, 1151, 1180, 1370),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna escobero 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 200, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 201 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Mueble interior escobero (solo Z1, alto 90, fondo 33)
for ref, z1 in [
    ("ACC_ESC300", 59),
    ("ACC_ESC350", 64),
    ("ACC_ESC400", 70),
    ("ACC_ESC450", 77),
    ("ACC_ESC500", 85),
    ("ACC_ESC600", 93),
]:
    products_to_add.append({
        "reference": ref, "name": "Mueble interior escobero",
        "programa": "ESTÁNDAR", "category": "ACCESORIOS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 201, "width": extract_width(ref), "height": 90, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z1, "Z3": z1, "Z4": z1, "Z5": z1, "Z6": z1, "Z7": z1, "Z8": z1, "Z9": z1, "Z10": z1, "Z11": z1, "Z12": z1}
    })

# Columna Frigo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CF1P600", 328, 339, 372, 382, 426, 432, 467, 476, 503, 504, 517, 590),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna Frigo 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 201, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna Frigo 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CF1P1P600", 329, 340, 373, 383, 427, 433, 468, 477, 504, 505, 518, 591),
    ("20CF1P1P750", 427, 442, 485, 498, 556, 562, 609, 620, 655, 657, 673, 768),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna Frigo 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 201, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1P1P600", 286, 295, 320, 327, 359, 372, 399, 406, 428, 434, 448, 515),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 Puerta + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 201, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 202 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 2 Puertas + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2P2P600", 338, 353, 382, 365, 400, 479, 519, 528, 559, 593, 625, 762),
    ("20CH2P2P900", 406, 423, 459, 438, 480, 575, 622, 634, 670, 712, 750, 915),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 Puertas + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 202, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Bax + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1PEBH1P600", 368, 377, 402, 408, 441, 454, 481, 488, 510, 516, 530, 596),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 Puerta extraible Bax + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 202, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Lux + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1PELH1P600", 395, 404, 429, 436, 468, 481, 508, 516, 538, 543, 558, 624),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 Puerta extraible Lux + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 202, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Bax + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1PEBH2P600", 441, 452, 483, 490, 529, 544, 577, 586, 612, 619, 636, 716),
    ("20CH1PEBH2P900", 534, 547, 584, 593, 640, 659, 698, 709, 741, 749, 770, 866),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 Puerta extraible Bax + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 202, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 203 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 1 Puerta extraible Lux + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1PELH2P600", 463, 474, 505, 512, 551, 566, 599, 608, 634, 641, 658, 738),
    ("20CH1PELH2P900", 556, 569, 606, 615, 662, 681, 720, 731, 763, 771, 792, 888),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 Puerta extraible Lux + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 203, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CB1P600", 489, 509, 546, 563, 614, 607, 646, 655, 686, 802, 841, 992),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 203, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CL1P600", 593, 614, 651, 668, 718, 712, 751, 760, 791, 906, 946, 1096),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 203, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CB1PABL600", 615, 635, 672, 689, 740, 733, 772, 781, 812, 928, 967, 1118),
    ("20CH4CB1PABL900", 738, 762, 806, 827, 888, 879, 926, 937, 974, 1114, 1160, 1342),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 203, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 204 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 4 cajones Lux + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CL1PABL600", 719, 740, 777, 794, 844, 838, 877, 886, 917, 1032, 1072, 1222),
    ("20CH4CL1PABL900", 863, 888, 932, 953, 1013, 1005, 1052, 1063, 1100, 1239, 1286, 1467),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 204, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CB2P600", 515, 537, 576, 584, 635, 650, 692, 702, 736, 875, 923, 1106),
    ("20CH4CB2P900", 617, 644, 692, 701, 762, 780, 830, 843, 883, 1050, 1108, 1327),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 204, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH4CL2P600", 620, 642, 680, 689, 740, 754, 797, 807, 841, 980, 1028, 1210),
    ("20CH4CL2P900", 743, 770, 816, 827, 888, 905, 956, 969, 1009, 1176, 1234, 1452),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 204, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CB1P600", 545, 543, 576, 549, 585, 607, 638, 646, 671, 709, 728, 750),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 204, "width": 60, "height": 200, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 200-204")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
