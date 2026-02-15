#!/usr/bin/env python3
"""
Process pages 175-179 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SEMICOLUMNAS DE 130cm (continuación)
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
# PAGE 175 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 2 puertas (vitrinas)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2V600", 387, 361, 385, 379, 408, 465, 501, 509, 538, 525, 538, 628),
    ("13SC2V700", 408, 392, 419, 418, 452, 485, 521, 529, 558, 560, 572, 663),
    ("13SC2V800", 434, 422, 452, 458, 496, 505, 541, 549, 578, 594, 607, 696),
    ("13SC2V900", 458, 455, 486, 499, 542, 553, 593, 603, 634, 631, 644, 732),
    ("13SC2V1000", 481, 487, 522, 538, 586, 613, 659, 670, 707, 666, 677, 765),
    ("13SC2V1200", 528, 548, 588, 615, 673, 652, 698, 710, 747, 747, 840, 834),
    ("13SC2V1300", 570, 592, 635, 665, 727, 704, 754, 767, 806, 794, 806, 900),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 175, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1PH600", 170, 174, 186, 185, 200, 202, 214, 217, 227, 232, 239, 270),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 175, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2PH600", 170, 174, 186, 185, 200, 202, 214, 217, 227, 232, 239, 270),
    ("13SC2PH900", 195, 202, 216, 206, 221, 245, 260, 265, 277, 306, 321, 382),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 175, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 176 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1VH600", 211, 215, 227, 226, 240, 243, 255, 258, 268, 273, 280, 311),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 176, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 vitrinas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2VH600", 226, 230, 242, 240, 255, 257, 270, 273, 282, 288, 295, 326),
    ("13SC2VH900", 284, 290, 305, 294, 309, 333, 349, 353, 365, 394, 410, 470),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 176, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 4 cajones 175mm BAX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC4CBH600", 333, 328, 345, 324, 341, 357, 373, 376, 389, 414, 423, 417),
    ("13SC4CBH900", 406, 401, 419, 398, 415, 431, 446, 449, 462, 487, 497, 490),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 175mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 176, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 177 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 4 cajones 175mm LUX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC4CLH600", 474, 468, 486, 465, 482, 497, 512, 517, 529, 554, 564, 558),
    ("13SC4CLH900", 552, 547, 565, 544, 561, 575, 591, 595, 608, 633, 643, 636),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 175mm LUX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 177, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 5 cajones 140mm BAX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC5CBH600", 392, 385, 407, 381, 402, 421, 441, 446, 461, 494, 505, 498),
    ("13SC5CBH900", 460, 454, 476, 449, 470, 489, 509, 515, 529, 562, 573, 566),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 140mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 177, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 5 cajones 140mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC5CLH600", 565, 559, 581, 554, 575, 594, 614, 618, 634, 666, 677, 670),
    ("13SC5CLH900", 660, 654, 676, 650, 671, 690, 710, 714, 730, 761, 773, 765),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 140mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 177, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 280 + 3 cajones 140mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G3CBH600", 347, 347, 366, 355, 377, 386, 404, 408, 423, 470, 485, 511),
    ("13SC1G3CBH900", 425, 425, 445, 434, 456, 465, 483, 487, 502, 549, 564, 590),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 280 + 3 cajones 140mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 177, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 178 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 1 cacerolero 280 + 3 cajones 140mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G3CLH600", 491, 492, 511, 500, 522, 531, 549, 553, 568, 615, 630, 656),
    ("13SC1G3CLH900", 571, 572, 591, 580, 602, 611, 629, 633, 648, 695, 710, 736),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 280 + 3 cajones 140mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 178, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 350 + 2 cajones 175mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G2CBH600", 318, 318, 338, 327, 349, 358, 376, 380, 395, 442, 457, 483),
    ("13SC1G2CBH900", 384, 384, 404, 393, 415, 424, 442, 446, 461, 508, 523, 549),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 350 + 2 cajones 175mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 178, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 350 + 2 cajones 175mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G2CLH600", 461, 462, 481, 469, 491, 501, 519, 523, 538, 585, 600, 626),
    ("13SC1G2CLH900", 531, 532, 551, 540, 562, 571, 589, 593, 608, 655, 670, 696),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 350 + 2 cajones 175mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 178, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 280 + 1 cajon 140mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G1CBH600", 331, 331, 351, 339, 361, 371, 389, 393, 407, 455, 469, 496),
    ("13SC1G1CBH900", 397, 397, 417, 405, 427, 437, 455, 459, 474, 521, 536, 562),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 280 + 1 cajon 140mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 178, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 179 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 2 caceroleros 280 + 1 cajon 140mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G1CLH600", 477, 478, 497, 485, 507, 517, 534, 539, 553, 601, 615, 642),
    ("13SC1G1CLH900", 547, 548, 567, 555, 578, 587, 605, 609, 624, 671, 686, 712),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 280 + 1 cajon 140mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 179, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 350mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2GBH600", 259, 266, 279, 290, 311, 301, 316, 319, 331, 379, 395, 456),
    ("13SC2GBH900", 314, 320, 334, 344, 365, 356, 371, 374, 385, 434, 449, 510),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 350mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 179, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 350mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2GLH600", 335, 340, 355, 365, 385, 376, 391, 395, 406, 454, 469, 530),
    ("13SC2GLH900", 396, 401, 416, 426, 446, 437, 452, 456, 467, 515, 530, 591),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 350mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 179, "width": extract_width(ref), "height": 130, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 175-179")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
