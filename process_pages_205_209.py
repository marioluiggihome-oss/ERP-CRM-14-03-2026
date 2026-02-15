#!/usr/bin/env python3
"""
Process pages 205-209 from TARIFA-TECNICA-ZONACOCINAS
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
# PAGE 205 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 5 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CL1P600", 675, 674, 708, 679, 716, 737, 769, 777, 801, 839, 858, 881),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 205, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Bax + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CB1PABL600", 671, 669, 702, 675, 711, 733, 764, 772, 797, 835, 854, 876),
    ("20CH5CB1PABL900", 819, 816, 857, 824, 867, 894, 933, 942, 972, 1018, 1041, 1068),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Bax + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 205, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Lux + horno 600mm + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CL1PABL600", 801, 800, 834, 805, 842, 863, 895, 903, 927, 965, 984, 1007),
    ("20CH5CL1PABL900", 977, 976, 1017, 983, 1027, 1053, 1091, 1102, 1131, 1177, 1200, 1228),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Lux + horno 600mm + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 205, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 5 cajones Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CB2P600", 570, 570, 607, 570, 606, 649, 685, 693, 721, 781, 809, 862),
    ("20CH5CB2P900", 684, 684, 728, 684, 727, 779, 822, 832, 866, 937, 970, 1034),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 205, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 206 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 5 cajones Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH5CL2P600", 701, 701, 737, 700, 737, 780, 816, 824, 852, 912, 940, 993),
    ("20CH5CL2P900", 842, 842, 885, 840, 885, 936, 979, 989, 1022, 1095, 1128, 1192),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 5 cajones Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 206, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CB1P600", 442, 461, 494, 499, 542, 550, 585, 593, 622, 687, 718, 839),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 206, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CL1P600", 523, 542, 574, 580, 623, 631, 666, 674, 702, 768, 799, 919),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 206, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CB1PABL600", 568, 587, 620, 625, 668, 676, 711, 719, 748, 813, 844, 965),
    ("20CH1G2CB1PABL900", 699, 722, 762, 768, 821, 832, 874, 885, 920, 1000, 1038, 1187),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 206, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 207 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CL1PABL600", 649, 668, 700, 706, 749, 757, 792, 800, 828, 894, 925, 1045),
    ("20CH1G2CL1PABL900", 798, 821, 861, 868, 921, 931, 974, 984, 1019, 1099, 1138, 1285),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 207, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CB2P600", 468, 488, 524, 520, 564, 592, 631, 641, 672, 759, 799, 951),
    ("20CH1G2CB2P900", 576, 601, 644, 639, 694, 728, 776, 788, 827, 934, 983, 1170),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 207, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH1G2CL2P600", 549, 569, 605, 601, 645, 673, 712, 722, 753, 840, 880, 1032),
    ("20CH1G2CL2P900", 675, 700, 744, 739, 793, 828, 876, 889, 926, 1033, 1082, 1270),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 207, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CB1P600", 461, 480, 515, 514, 556, 574, 608, 616, 645, 728, 761, 897),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 207, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 208 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CL1P600", 529, 541, 569, 572, 609, 610, 639, 647, 670, 737, 763, 852),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 208, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CB1PABL600", 580, 588, 618, 623, 662, 659, 690, 697, 721, 781, 806, 896),
    ("20CH2G1CB1PABL900", 713, 723, 761, 766, 814, 811, 849, 858, 887, 961, 992, 1102),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 208, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CL1PABL600", 655, 667, 695, 698, 735, 736, 765, 773, 796, 863, 889, 978),
    ("20CH2G1CL1PABL900", 806, 820, 855, 859, 904, 905, 942, 951, 979, 1062, 1094, 1202),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 208, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CB2P600", 479, 490, 523, 518, 558, 576, 610, 618, 646, 729, 762, 883),
    ("20CH2G1CB2P900", 579, 593, 633, 626, 675, 698, 738, 748, 781, 882, 922, 1068),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 208, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 209 - COLUMNAS DE 200cm FONDO 58cm
# ============================================

# Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2G1CL2P600", 563, 573, 606, 601, 641, 659, 694, 702, 729, 812, 846, 966),
    ("20CH2G1CL2P900", 687, 699, 739, 733, 781, 804, 847, 857, 889, 990, 1032, 1179),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 209, "width": extract_width(ref), "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Bax + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2GB1P600", 396, 412, 441, 435, 470, 492, 524, 531, 557, 571, 594, 685),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Bax + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 209, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Lux + horno 600mm + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2GL1P600", 453, 469, 499, 492, 527, 550, 582, 589, 613, 628, 652, 741),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Lux + horno 600mm + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 209, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Bax + horno 600mm + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20CH2GB1PABL600", 522, 538, 567, 561, 596, 618, 650, 657, 683, 697, 720, 811),
    ("20CH2GB1PABL900", 642, 661, 697, 690, 734, 761, 799, 808, 839, 858, 886, 997),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Bax + horno 600mm + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 209, "width": extract_width(ref), "height": 200, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 205-209")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
