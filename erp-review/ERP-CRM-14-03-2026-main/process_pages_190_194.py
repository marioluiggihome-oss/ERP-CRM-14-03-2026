#!/usr/bin/env python3
"""
Process pages 190-194 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SEMICOLUMNAS DE 160cm (continuación)
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
# PAGE 190 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC2V600", 487, 486, 523, 501, 541, 602, 648, 660, 697, 733, 771, 932),
    ("16SC2V700", 517, 528, 570, 551, 600, 644, 694, 706, 745, 782, 830, 980),
    ("16SC2V800", 546, 569, 613, 602, 657, 679, 730, 742, 783, 830, 875, 1026),
    ("16SC2V900", 577, 613, 663, 657, 717, 735, 790, 804, 849, 881, 916, 1075),
    ("16SC2V1000", 607, 658, 712, 709, 777, 790, 851, 865, 913, 929, 965, 1123),
    ("16SC2V1200", 667, 741, 804, 814, 895, 883, 952, 968, 1021, 1047, 1053, 1218),
    ("16SC2V1300", 693, 767, 830, 840, 921, 909, 978, 994, 1047, 1053, 1087, 1244),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 190, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1PH600", 224, 230, 246, 254, 276, 287, 306, 311, 326, 325, 334, 377),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 190, "width": 60, "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC2PH600", 253, 263, 281, 274, 296, 362, 389, 395, 418, 425, 444, 533),
    ("16SC2PH900", 282, 294, 315, 307, 332, 405, 436, 442, 467, 476, 497, 597),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 190, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1VH600", 299, 304, 320, 317, 421, 339, 357, 361, 373, 380, 390, 430),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 190, "width": 60, "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 191 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 2 vitrinas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC2VH600", 286, 297, 318, 310, 335, 409, 440, 446, 472, 481, 502, 602),
    ("16SC2VH900", 320, 332, 356, 347, 374, 458, 492, 501, 529, 538, 561, 674),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 191, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 4 cajones 200mm BAX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC4CBH600", 421, 440, 470, 491, 534, 523, 554, 561, 587, 717, 755, 898),
    ("16SC4CBH900", 501, 523, 559, 584, 636, 621, 660, 669, 700, 856, 901, 1073),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 200mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 191, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 4 cajones 200mm LUX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC4CLH600", 585, 603, 633, 654, 698, 685, 717, 725, 750, 880, 918, 1061),
    ("16SC4CLH900", 702, 724, 760, 785, 837, 822, 861, 870, 900, 1056, 1102, 1273),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 200mm LUX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 191, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 5 cajones 200mm BAX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC5CBH600", 476, 468, 494, 463, 488, 510, 534, 539, 558, 596, 610, 676),
    ("16SC5CBH900", 566, 557, 588, 551, 581, 607, 635, 641, 663, 709, 725, 805),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 200mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 191, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 192 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 5 cajones 200mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC5CLH600", 681, 674, 700, 669, 694, 716, 740, 745, 763, 800, 814, 805),
    ("16SC5CLH900", 804, 795, 826, 789, 819, 845, 873, 879, 901, 944, 961, 950),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 200mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 192, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 400 + 3 cajones 200mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G3CBH600", 437, 436, 460, 447, 475, 483, 507, 512, 529, 581, 600, 630),
    ("16SC1G3CBH900", 525, 523, 552, 537, 570, 579, 608, 614, 635, 697, 720, 756),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 400 + 3 cajones 200mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 192, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 400 + 3 cajones 200mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G3CLH600", 610, 609, 633, 620, 648, 655, 679, 684, 702, 753, 772, 803),
    ("16SC1G3CLH900", 732, 730, 759, 744, 777, 786, 815, 821, 842, 904, 927, 963),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 400 + 3 cajones 200mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 192, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero 500 + 2 cajones 250mm BAX + horno 600mm (NOTE: ref shows 14SC but categorized as 160cm)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G2CBH600", 458, 458, 487, 470, 502, 516, 541, 547, 569, 637, 658, 696),
    ("16SC1G2CBH900", 553, 553, 582, 565, 597, 611, 637, 643, 664, 732, 753, 791),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 500 + 2 cajones 250mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 192, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 193 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 1 cacerolero 400 + 2 cajones 250mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G2CLH600", 664, 665, 692, 676, 708, 721, 747, 753, 774, 842, 863, 901),
    ("16SC1G2CLH900", 765, 767, 794, 777, 809, 823, 848, 854, 875, 943, 965, 1002),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero 400 + 2 cajones 250mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 193, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 400 + 1 cajon 200mm BAX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G1CBH600", 481, 481, 511, 494, 527, 541, 568, 575, 597, 668, 691, 730),
    ("16SC1G1CBH900", 581, 581, 611, 594, 627, 641, 668, 675, 697, 768, 791, 830),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 400 + 1 cajon 200mm BAX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 193, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 caceroleros 400 + 1 cajon 200mm LUX + horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G1CLH600", 697, 699, 727, 710, 743, 757, 784, 791, 813, 884, 907, 946),
    ("16SC1G1CLH900", 803, 805, 833, 816, 849, 864, 891, 897, 919, 991, 1013, 1053),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 caceroleros 400 + 1 cajon 200mm LUX + horno 600mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 193, "width": extract_width(ref), "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1PHM600", 199, 206, 216, 214, 226, 237, 249, 252, 261, 266, 276, 311),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 193, "width": 60, "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 194 - SEMICOLUMNAS DE 160cm
# ============================================

# Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC2PHM600", 227, 230, 241, 245, 259, 290, 306, 310, 322, 360, 376, 437),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 194, "width": 60, "height": 160, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("16SC1G1CLHM600", 382, 385, 399, 397, 414, 415, 427, 430, 441, 481, 494, 527),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 160cm",
        "sourcePage": 194, "width": 60, "height": 160, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 190-194")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
