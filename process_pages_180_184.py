#!/usr/bin/env python3
"""
Process pages 180-184 from TARIFA-TECNICA-ZONACOCINAS
Pages 180-181: SEMICOLUMNAS DE 130cm (continuación)
Pages 182-184: SEMICOLUMNAS DE 140cm
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
# PAGE 180 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1PHM600", 151, 154, 161, 166, 176, 180, 187, 189, 195, 211, 218, 249),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 180, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2PHM600", 175, 177, 185, 192, 204, 226, 238, 242, 252, 289, 302, 354),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 180, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero BAX + horno 600mm / 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1GBHM600", 184, 187, 194, 200, 209, 205, 212, 214, 219, 244, 252, 281),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero BAX + horno 600mm / 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 180, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero LUX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1GLHM600", 221, 224, 231, 236, 247, 242, 249, 251, 256, 280, 289, 319),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero LUX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 180, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 181 - SEMICOLUMNAS DE 130cm
# ============================================

# Semicolumna 1 cacerolero +1 cajón BAX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G1CBHM600", 245, 248, 255, 260, 270, 266, 273, 275, 280, 305, 313, 342),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero +1 cajón BAX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 181, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1G1CLHM600", 310, 313, 320, 326, 420, 331, 338, 340, 345, 370, 378, 408),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 cacerolero + 1 cajón LUX + horno 460mm + micro 400mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 181, "width": 60, "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 182 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1P300", 182, 189, 205, 195, 212, 251, 271, 276, 292, 307, 322, 391),
    ("14SC1P350", 193, 201, 218, 210, 230, 263, 285, 289, 306, 321, 341, 405),
    ("14SC1P400", 205, 212, 231, 226, 249, 272, 293, 298, 316, 420, 355, 419),
    ("14SC1P450", 215, 224, 245, 242, 267, 288, 312, 317, 420, 350, 364, 433),
    ("14SC1P500", 231, 240, 264, 261, 290, 310, 335, 341, 361, 369, 383, 450),
    ("14SC1P600", 254, 264, 290, 293, 328, 337, 365, 372, 395, 397, 412, 478),
    ("14SC1P650", 276, 286, 312, 315, 350, 359, 387, 394, 417, 419, 434, 500),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 182, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2P600", 297, 312, 343, 323, 358, 436, 476, 486, 517, 548, 580, 716),
    ("14SC2P700", 320, 420, 371, 355, 395, 460, 503, 512, 546, 576, 617, 744),
    ("14SC2P800", 342, 358, 396, 385, 431, 477, 520, 530, 565, 605, 643, 772),
    ("14SC2P900", 368, 383, 425, 419, 470, 512, 560, 571, 608, 635, 666, 801),
    ("14SC2P1000", 391, 408, 455, 450, 508, 547, 599, 610, 651, 665, 695, 828),
    ("14SC2P1200", 436, 456, 508, 516, 584, 602, 658, 672, 717, 722, 752, 884),
    ("14SC2P1300", 480, 500, 552, 560, 628, 646, 702, 716, 761, 767, 796, 928),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 182, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1V300", 239, 238, 254, 246, 263, 288, 308, 313, 329, 343, 359, 428),
    ("14SC1V350", 252, 256, 274, 267, 287, 306, 327, 332, 349, 364, 384, 448),
    ("14SC1V400", 265, 274, 293, 289, 311, 320, 342, 348, 364, 385, 404, 468),
    ("14SC1V450", 277, 292, 313, 310, 420, 343, 366, 373, 392, 405, 420, 487),
    ("14SC1V500", 293, 315, 337, 420, 365, 371, 396, 402, 423, 429, 444, 511),
    ("14SC1V600", 318, 350, 377, 381, 415, 411, 439, 446, 468, 470, 485, 552),
    ("14SC1V650", 351, 382, 410, 414, 447, 443, 471, 479, 501, 503, 518, 585),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 182, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 183 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2V600", 413, 412, 443, 424, 459, 510, 549, 560, 591, 622, 653, 790),
    ("14SC2V700", 438, 447, 483, 467, 508, 546, 588, 599, 632, 663, 704, 831),
    ("14SC2V800", 463, 482, 520, 510, 557, 575, 618, 629, 664, 704, 741, 869),
    ("14SC2V900", 489, 520, 562, 557, 608, 623, 670, 681, 719, 747, 776, 911),
    ("14SC2V1000", 515, 558, 604, 601, 658, 670, 721, 733, 774, 788, 818, 951),
    ("14SC2V1200", 565, 628, 681, 690, 758, 749, 806, 820, 865, 870, 899, 1054),
    ("14SC2V1300", 587, 650, 704, 712, 780, 771, 828, 842, 887, 893, 921, 1054),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 183, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1PH600", 188, 193, 207, 213, 232, 242, 257, 261, 274, 273, 280, 317),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Izquierda/Derecha) + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 183, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2PH600", 214, 223, 238, 232, 251, 307, 330, 335, 354, 360, 376, 452),
    ("14SC2PH900", 240, 249, 267, 260, 281, 343, 369, 375, 396, 403, 421, 506),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 183, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC1VH600", 253, 258, 270, 269, 286, 288, 302, 306, 316, 322, 330, 365),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Izquierda/Derecha) + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 183, "width": 60, "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 184 - SEMICOLUMNAS DE 140cm
# ============================================

# Semicolumna 2 vitrinas + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC2VH600", 242, 252, 269, 262, 284, 346, 373, 378, 400, 407, 425, 510),
    ("14SC2VH900", 271, 282, 302, 294, 318, 388, 417, 424, 448, 456, 476, 571),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 vitrinas + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 184, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 4 cajones 200mm BAX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC4CBH600", 357, 373, 398, 416, 453, 443, 469, 476, 498, 608, 639, 761),
    ("14SC4CBH900", 425, 444, 474, 495, 539, 527, 559, 567, 593, 726, 764, 910),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 200mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 184, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 4 cajones 200mm LUX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC4CLH600", 496, 511, 537, 554, 591, 581, 608, 614, 635, 746, 778, 899),
    ("14SC4CLH900", 595, 614, 644, 665, 709, 697, 730, 737, 762, 895, 934, 1079),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 4 cajones 200mm LUX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 184, "width": extract_width(ref), "height": 140, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 5 cajones 160mm LUX + horno 600mm / 460mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SC5CBH600", 403, 397, 419, 393, 414, 433, 453, 457, 473, 505, 517, 573),
    ("14SC5CBH900", 480, 472, 499, 467, 492, 515, 539, 544, 562, 601, 615, 682),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 5 cajones 160mm BAX + horno 600mm / 460mm",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 140cm",
        "sourcePage": 184, "width": extract_width(ref), "height": 140, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 180-184")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
