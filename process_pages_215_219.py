#!/usr/bin/env python3
"""
Process pages 215-219 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - COLUMNAS - ALTO 200cm FONDO 58cm
Columnas rincón, decorativas, botelleros
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
# PAGE 215 - COLUMNAS 2 CACEROLEROS + HORNO + MICRO (continuación)
# ============================================

# Columna 2 caceroleros Bax + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GB1PABL600", 506, 521, 543, 547, 575, 581, 604, 610, 629, 696, 719, 806),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Bax + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 215, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Lux + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GL1PABL600", 564, 578, 600, 604, 633, 637, 662, 667, 686, 754, 776, 864),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Lux + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 215, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Bax + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GB2P600", 405, 420, 444, 446, 477, 508, 538, 545, 568, 638, 670, 786),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Bax + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 215, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Lux + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GL2P600", 463, 478, 502, 503, 535, 565, 596, 602, 625, 696, 727, 843),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Lux + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 215, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 216 - COLUMNAS RINCÓN ANGULAR
# ============================================

# Columna rincón angular 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRA2P2P930", 671, 691, 725, 712, 763, 840, 893, 905, 946, 981, 1010, 1160),
    ("20CRA2P2P1030", 715, 735, 769, 756, 807, 884, 937, 949, 990, 1025, 1054, 1204),
    ("20CRA2P2P1130", 770, 790, 823, 811, 862, 939, 991, 1004, 1045, 1079, 1109, 1259),
    ("20CRA2P2P1230", 819, 839, 873, 860, 911, 988, 1041, 1053, 1094, 1129, 1158, 1308),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón angular 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 216, "width": 93, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRA2P930", 722, 741, 709, 696, 748, 824, 877, 889, 930, 965, 994, 1145),
    ("20CRA2P1030", 781, 802, 767, 753, 809, 891, 948, 962, 1006, 1043, 1075, 1237),
    ("20CRA2P1130", 845, 867, 829, 815, 875, 964, 1025, 1040, 1088, 1128, 1162, 1338),
    ("20CRA2P1230", 940, 964, 922, 906, 973, 1072, 1140, 1156, 1209, 1254, 1292, 1486),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón angular 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 216, "width": 93, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna rincón angular 1 puerta (Derecha/Izquierda) - some values empty
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRA1P930", 681, 700, 668, 655, 707, 783, 836, 848, 889, 924, 953, 0),
    ("20CRA1P1030", 741, 761, 726, 712, 768, 851, 907, 921, 965, 0, 0, 0),
    ("20CRA1P1130", 804, 826, 788, 774, 834, 923, 984, 999, 0, 0, 0, 0),
    ("20CRA1P1230", 899, 923, 881, 865, 932, 0, 0, 0, 0, 0, 0, 0),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón angular 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 216, "width": 93, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna rincón lineal 1 puerta + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRC1P1P900", 419, 434, 449, 433, 463, 516, 548, 548, 572, 632, 648, 722),
    ("20CRC1P1P950", 436, 449, 466, 449, 479, 532, 564, 564, 589, 648, 665, 738),
    ("20CRC1P1P1000", 444, 459, 477, 463, 496, 533, 566, 566, 591, 659, 676, 750),
    ("20CRC1P1P1050", 479, 492, 513, 503, 540, 563, 595, 595, 621, 698, 714, 786),
    ("20CRC1P1P1100", 487, 502, 524, 518, 559, 581, 616, 617, 645, 710, 726, 798),
    ("20CRC1P1P1150", 496, 511, 537, 532, 576, 606, 646, 648, 678, 721, 737, 810),
    ("20CRC1P1P1200", 509, 526, 555, 559, 610, 614, 656, 658, 690, 742, 757, 828),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón lineal 1 puerta + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 216, "width": 90, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 217 - COLUMNAS RINCÓN LINEAL
# ============================================

# Columna rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRC1P900", 382, 397, 413, 396, 426, 479, 511, 511, 536, 595, 611, 686),
    ("20CRC1P950", 399, 413, 429, 413, 442, 496, 527, 527, 552, 611, 628, 701),
    ("20CRC1P1000", 407, 422, 440, 426, 459, 497, 529, 529, 554, 623, 639, 713),
    ("20CRC1P1050", 442, 456, 477, 466, 503, 526, 559, 559, 584, 662, 677, 750),
    ("20CRC1P1100", 450, 465, 487, 481, 522, 544, 580, 581, 608, 673, 689, 761),
    ("20CRC1P1150", 459, 475, 500, 496, 540, 569, 609, 611, 642, 685, 700, 773),
    ("20CRC1P1200", 473, 489, 519, 522, 573, 578, 620, 622, 653, 706, 720, 792),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón lineal 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 217, "width": 90, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna rincón lineal 2 puertas + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRC2P2P1200", 601, 621, 655, 659, 720, 725, 774, 777, 814, 876, 893, 978),
    ("20CRC2P2P1300", 709, 732, 773, 778, 849, 855, 914, 917, 961, 1034, 1054, 1154),
    ("20CRC2P2P1400", 837, 864, 913, 918, 1002, 1009, 1078, 1082, 1133, 1220, 1244, 1361),
    ("20CRC2P2P1500", 987, 1020, 1077, 1083, 1183, 1191, 1272, 1276, 1337, 1439, 1468, 1606),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón lineal 2 puertas + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 217, "width": 120, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 218 - COLUMNAS DE 200cm DECORATIVOS
# ============================================

# Columna rincón lineal 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CRC2P1200", 558, 577, 612, 616, 676, 681, 731, 733, 771, 833, 850, 934),
    ("20CRC2P1300", 658, 681, 722, 727, 798, 804, 863, 866, 909, 982, 1003, 1102),
    ("20CRC2P1400", 776, 804, 852, 857, 942, 949, 1018, 1021, 1073, 1159, 1183, 1301),
    ("20CRC2P1500", 916, 949, 1006, 1012, 1112, 1120, 1201, 1205, 1266, 1368, 1397, 1535),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna rincón lineal 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm DECORATIVOS",
        "sourcePage": 218, "width": 120, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna decorativo 4 estantes
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CDEC300", 545, 611, 507, 445, 534, 661, 751, 661, 751, 675, 675, 675),
    ("20CDEC350", 562, 628, 524, 462, 551, 697, 790, 697, 790, 700, 700, 700),
    ("20CDEC400", 607, 682, 561, 491, 592, 747, 852, 747, 852, 742, 742, 742),
    ("20CDEC450", 634, 714, 587, 514, 620, 782, 891, 782, 891, 779, 779, 779),
    ("20CDEC500", 652, 737, 604, 528, 637, 810, 924, 810, 924, 809, 809, 809),
    ("20CDEC600", 685, 771, 636, 556, 672, 858, 980, 858, 980, 861, 861, 861),
    ("20CDEC700", 795, 894, 738, 645, 780, 996, 1137, 996, 1137, 998, 998, 998),
    ("20CDEC800", 922, 1038, 856, 748, 905, 1155, 1318, 1155, 1318, 1158, 1158, 1158),
    ("20CDEC900", 1069, 1204, 993, 867, 1050, 1340, 1529, 1340, 1529, 1343, 1343, 1343),
    ("20CDEC1000", 1240, 1396, 1152, 1006, 1218, 1554, 1774, 1554, 1774, 1558, 1558, 1558),
    ("20CDEC1100", 1439, 1620, 1336, 1167, 1412, 1803, 2058, 1803, 2058, 1808, 1808, 1808),
    ("20CDEC1200", 1669, 1879, 1550, 1354, 1638, 2091, 2387, 2091, 2387, 2097, 2097, 2097),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna decorativo 4 estantes",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm DECORATIVOS",
        "sourcePage": 218, "width": 30, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna botellero cuadros
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CBOT150", 602, 668, 564, 501, 591, 718, 807, 718, 807, 731, 731, 731),
    ("20CBOT300", 820, 920, 775, 682, 815, 1026, 1165, 1026, 1165, 1036, 1036, 1036),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna botellero cuadros",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm DECORATIVOS",
        "sourcePage": 218, "width": 15, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 219 - COLUMNAS DECORATIVOS (continuación)
# ============================================

# Columna decorativo terminal
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CTER300", 393, 249, 311, 248, 311, 355, 411, 355, 411, 466, 466, 466),
    ("20CTER500", 472, 299, 373, 298, 373, 426, 493, 426, 493, 559, 559, 559),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna decorativo terminal",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm DECORATIVOS",
        "sourcePage": 219, "width": 30, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

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
print(f"RESUMEN - PÁGINAS 215-219")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created}")
print(f"Productos actualizados: {updated}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
