#!/usr/bin/env python3
"""
Process pages 225-229 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - COLUMNAS DE 220cm FONDO 58cm - Con Horno
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
# PAGE 225 - COLUMNAS CON HORNO 220cm
# ============================================

# Columna 1 Puerta + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1P1P600", 311, 320, 347, 360, 398, 416, 448, 456, 482, 481, 495, 568),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 Puerta + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 225, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 Puertas + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH2P2P600", 363, 378, 411, 398, 435, 546, 593, 605, 642, 654, 685, 837),
    ("22CH2P2P900", 436, 454, 493, 478, 522, 655, 712, 726, 770, 785, 822, 1004),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 2 Puertas + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 225, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Bax + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1PEB1P600", 396, 405, 432, 445, 483, 501, 533, 541, 567, 566, 580, 653),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 Puerta extraible Bax + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 225, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Lux + Horno + 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1PEL1P600", 396, 405, 432, 445, 483, 501, 533, 541, 567, 566, 580, 653),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 Puerta extraible Lux + Horno + 1 Puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 225, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 226 - COLUMNAS EXTRAIBLES + HORNO
# ============================================

# Columna 1 Puerta extraible Bax + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1PEBH2P600", 457, 471, 504, 491, 528, 639, 687, 698, 735, 748, 778, 930),
    ("22CH1PEBH2P900", 539, 556, 595, 580, 623, 755, 810, 824, 867, 882, 918, 1098),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 Puerta extraible Bax + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 226, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 Puerta extraible Lux + Horno + 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1PELH2P600", 593, 611, 650, 635, 679, 813, 869, 883, 927, 942, 979, 1162),
    ("22CH1PELH2P900", 712, 733, 780, 762, 815, 975, 1043, 1060, 1113, 1131, 1175, 1394),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 Puerta extraible Lux + Horno + 2 Puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 226, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno 600mm + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CB1P600", 513, 533, 572, 597, 652, 651, 694, 705, 739, 848, 887, 1046),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Bax + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 226, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno 600mm + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CL1P600", 617, 638, 677, 702, 757, 756, 799, 810, 844, 953, 992, 1150),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Lux + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 226, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 227 - COLUMNAS 4 CAJONES + HORNO + ABATIBLE
# ============================================

# Columna 4 cajones Bax + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CB1PABL600", 650, 670, 709, 734, 789, 788, 831, 841, 876, 985, 1024, 1182),
    ("22CH4CB1PABL900", 780, 804, 851, 881, 946, 945, 997, 1009, 1051, 1182, 1229, 1419),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Bax + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 227, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CL1PABL600", 754, 775, 814, 839, 894, 893, 936, 946, 981, 1090, 1129, 1286),
    ("22CH4CL1PABL900", 905, 930, 977, 1007, 1072, 1071, 1123, 1135, 1177, 1308, 1355, 1544),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Lux + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 227, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CB2P600", 540, 563, 604, 615, 671, 716, 767, 779, 819, 936, 983, 1180),
    ("22CH4CB2P900", 642, 670, 718, 732, 798, 852, 912, 927, 975, 1113, 1170, 1404),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 227, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH4CL2P600", 645, 668, 709, 720, 775, 821, 872, 884, 924, 1041, 1087, 1284),
    ("22CH4CL2P900", 774, 801, 851, 864, 930, 985, 1046, 1061, 1109, 1249, 1304, 1541),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 4 cajones Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 227, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 228 - COLUMNAS 5 CAJONES + HORNO
# ============================================

# Columna 5 cajones Bax + horno 600mm + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CB1P600", 573, 572, 609, 587, 628, 653, 690, 698, 727, 755, 774, 803),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Bax + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 228, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Lux + horno 600mm + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CL1P600", 705, 704, 739, 718, 759, 784, 820, 828, 858, 886, 904, 933),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Lux + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 228, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Bax + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CB1PABL600", 710, 709, 746, 723, 764, 790, 826, 835, 863, 891, 910, 940),
    ("22CH5CB1PABL900", 852, 851, 895, 868, 917, 948, 992, 1002, 1036, 1070, 1092, 1128),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Bax + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 228, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Lux + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CL1PABL600", 841, 840, 876, 855, 896, 921, 957, 965, 994, 1023, 1041, 1070),
    ("22CH5CL1PABL900", 1009, 1008, 1051, 1026, 1075, 1105, 1148, 1158, 1193, 1227, 1249, 1284),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Lux + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 228, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 229 - COLUMNAS 5 CAJONES + HORNO + 2 PUERTAS / CACEROLEROS
# ============================================

# Columna 5 cajones Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CB2P600", 601, 603, 642, 606, 647, 719, 763, 774, 807, 842, 868, 938),
    ("22CH5CB2P900", 721, 723, 770, 727, 776, 863, 916, 929, 969, 1011, 1042, 1125),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 229, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH5CL2P600", 731, 733, 773, 737, 777, 851, 894, 904, 939, 973, 1000, 1069),
    ("20CH5CL2P900", 877, 879, 927, 885, 932, 1021, 1072, 1085, 1126, 1168, 1200, 1283),  # Note: Reference starts with 20
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 5 cajones Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 229, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta (Der/Izq)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1G2CB1P600", 466, 485, 520, 533, 581, 594, 633, 644, 674, 733, 763, 891),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 229, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta (Der/Izq)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("22CH1G2CL1P600", 547, 566, 601, 614, 662, 675, 715, 725, 755, 814, 845, 972),
]:
    products_to_add.append({
        "reference": ref, "code": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta (Der/Izq)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 220cm FONDO 58cm",
        "sourcePage": 229, "width": 60, "height": 220, "depth": 58, "module": "montada",
        "points": z1, "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
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
print(f"RESUMEN - PÁGINAS 225-229")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created}")
print(f"Productos actualizados: {updated}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
