#!/usr/bin/env python3
"""
Process pages 185-189 from TARIFA-TECNICA-ZONACOCINAS
Pages 185-188: SEMICOLUMNAS DE 140cm (continuación)
Page 189: SEMICOLUMNAS DE 160cm
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
# PAGE 185 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 5 cajones 160mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC5CLH600", 578, 571, 593, 567, 588, 607, 627, 631, 647, 678, 690, 683),
    ("14SC5CLH900", 681, 674, 700, 669, 694, 716, 740, 745, 763, 800, 814, 805),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 160mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 185, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 320 + 3 cajones 160mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G3CBH600", 364, 363, 383, 373, 396, 402, 422, 426, 441, 484, 500, 525),
    ("14SC1G3CBH900", 437, 436, 460, 447, 475, 483, 507, 512, 529, 581, 600, 630),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 320 + 3 cajones 160mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 185, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 320 + 3 cajones 160mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G3CLH600", 508, 507, 527, 517, 540, 546, 566, 570, 585, 628, 644, 669),
    ("14SC1G3CLH900", 610, 609, 633, 620, 648, 655, 679, 684, 702, 753, 772, 803),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 320 + 3 cajones 160mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 185, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 400 + 2 cajones 200mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G2CBH600", 382, 382, 406, 392, 418, 430, 451, 456, 474, 530, 548, 580),
    ("14SC1G2CBH900", 461, 461, 485, 471, 498, 509, 530, 536, 553, 610, 627, 659),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 400 + 2 cajones 200mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 185, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 186 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 1 cacerolero 400 + 2 cajones 200mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G2CLH600", 553, 554, 577, 563, 590, 601, 622, 627, 645, 702, 719, 751),
    ("14SC1G2CLH900", 638, 639, 662, 648, 674, 685, 707, 712, 730, 786, 804, 835),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 400 + 2 cajones 200mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 186, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 320 + 1 cajon 160mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G1CBH600", 401, 401, 426, 411, 439, 451, 474, 479, 497, 557, 576, 609),
    ("14SC1G1CBH900", 484, 484, 509, 495, 523, 534, 557, 562, 581, 640, 659, 692),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 320 + 1 cajon 160mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 186, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 320 + 1 cajon 160mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G1CLH600", 581, 582, 606, 591, 619, 631, 654, 659, 677, 737, 755, 789),
    ("14SC1G1CLH900", 669, 671, 695, 680, 708, 720, 742, 747, 766, 826, 844, 877),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 320 + 1 cajon 160mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 186, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 400mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2GBH600", 278, 291, 308, 303, 323, 343, 362, 368, 382, 392, 407, 468),
    ("14SC2GBH900", 328, 343, 363, 358, 382, 405, 427, 434, 451, 462, 481, 553),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 400mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 186, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 187 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 2 caceroleros 400mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2GLH600", 355, 366, 384, 379, 400, 420, 439, 443, 459, 467, 484, 544),
    ("14SC2GLH900", 426, 440, 461, 455, 480, 504, 527, 532, 551, 561, 581, 653),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 400mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 187, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 puerta + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1PHM600", 167, 173, 182, 180, 190, 200, 209, 212, 219, 224, 232, 261),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 187, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2PHM600", 191, 193, 203, 206, 217, 244, 257, 260, 271, 302, 316, 368),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 187, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero BAX + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1GBHM600", 201, 206, 215, 212, 223, 232, 243, 245, 252, 256, 265, 295),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero BAX + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 187, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 188 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 1 cacerolero LUX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1GLHM600", 237, 244, 252, 250, 259, 270, 279, 281, 289, 294, 301, 332),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero LUX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 188, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero + 1 cajón BAX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G1CBHM600", 250, 252, 263, 263, 275, 277, 288, 290, 298, 333, 342, 372),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero + 1 cajón BAX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 188, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1G1CLHM600", 321, 323, 335, 334, 348, 349, 359, 361, 371, 404, 415, 443),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 188, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 189 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1P300", 214, 223, 242, 230, 250, 296, 320, 326, 344, 362, 380, 461),
    ("16SC1P350", 228, 237, 258, 248, 271, 310, 336, 341, 361, 379, 403, 478),
    ("16SC1P400", 242, 250, 273, 266, 294, 321, 346, 352, 373, 396, 419, 494),
    ("16SC1P450", 254, 264, 289, 285, 315, 339, 366, 374, 396, 413, 430, 510),
    ("16SC1P500", 273, 284, 311, 309, 342, 366, 395, 403, 426, 435, 452, 532),
    ("16SC1P600", 300, 311, 342, 346, 387, 398, 431, 439, 466, 468, 486, 564),
    ("16SC1P650", 326, 421, 368, 372, 413, 424, 457, 465, 492, 494, 512, 590),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 189, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC2P600", 345, 362, 398, 375, 415, 505, 552, 564, 599, 636, 672, 831),
    ("16SC2P700", 371, 390, 430, 412, 458, 533, 583, 594, 633, 669, 716, 864),
    ("16SC2P800", 397, 415, 459, 447, 499, 553, 603, 615, 655, 702, 745, 895),
    ("16SC2P900", 426, 445, 493, 486, 546, 594, 649, 663, 705, 737, 772, 929),
    ("16SC2P1000", 453, 474, 527, 523, 590, 635, 694, 708, 755, 771, 806, 961),
    ("16SC2P1200", 505, 529, 590, 598, 677, 698, 764, 780, 832, 838, 872, 1026),
    ("16SC2P1300", 557, 580, 641, 649, 728, 749, 815, 831, 883, 889, 923, 1077),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 189, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1V300", 282, 281, 300, 290, 310, 339, 363, 369, 388, 405, 424, 506),
    ("16SC1V350", 297, 302, 323, 315, 338, 361, 385, 392, 411, 430, 453, 529),
    ("16SC1V400", 312, 323, 346, 341, 367, 378, 404, 410, 430, 455, 477, 553),
    ("16SC1V450", 327, 344, 369, 366, 396, 405, 432, 440, 462, 478, 496, 575),
    ("16SC1V500", 346, 372, 398, 396, 431, 437, 467, 475, 499, 507, 524, 603),
    ("16SC1V600", 375, 413, 445, 450, 489, 484, 518, 527, 553, 555, 572, 652),
    ("16SC1V650", 414, 451, 483, 488, 528, 523, 556, 565, 591, 593, 611, 690),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 189, "width": extract_width(ref), "height": 160, "depth": 58,
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
    product["visualType"] = "semicolumna"
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
print(f"RESUMEN - PÁGINAS 185-189")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
