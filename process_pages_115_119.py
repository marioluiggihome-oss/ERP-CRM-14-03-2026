#!/usr/bin/env python3
"""
Process pages 115-118 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 58cm + DECORATIVOS
Page 119 is a cover page for MUEBLES BAJOS (no products)
"""

import json
import os
from pymongo import MongoClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
if MONGO_URL.startswith('"'):
    MONGO_URL = MONGO_URL.strip('"')
if DB_NAME.startswith('"'):
    DB_NAME = DB_NAME.strip('"')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Load existing valid references
with open('/app/valid_references.json', 'r') as f:
    valid_references = json.load(f)

initial_count = len(valid_references)
print(f"Referencias válidas iniciales: {initial_count}")

products_to_add = []

# ============================================
# PAGE 115 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 58cm
# ============================================

# Sobremódulo horno 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEH1V600", 257, 257, 272, 278, 297, 290, 307, 311, 323, 320, 328, 364),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 115,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 2 Vitrinas (Note: reference is 14SEH12V600 in the PDF)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEH2V600", 324, 300, 318, 310, 330, 356, 380, 386, 405, 407, 422, 499),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 2 Vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 115,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERA2P58630", 405, 417, 441, 427, 454, 527, 560, 569, 595, 598, 618, 723),
    ("14SERA2P58730", 431, 444, 470, 455, 484, 563, 599, 608, 636, 639, 661, 774),
    ("14SERA2P58830", 460, 473, 501, 486, 517, 602, 641, 651, 681, 684, 708, 830),
    ("14SERA2P58930", 490, 506, 536, 517, 552, 645, 687, 697, 730, 733, 759, 891),
    ("14SERA2P581030", 524, 539, 573, 553, 590, 690, 734, 747, 782, 786, 813, 956),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 115,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERA1P58630", 323, 332, 350, 339, 382, 415, 440, 458, 465, 488, 483, 562),
    ("14SERA1P58730", 362, 371, 389, 378, 421, 454, 478, 497, 504, 527, 521, 600),
    ("14SERA1P58830", 401, 409, 428, 417, 460, 493, 517, 536, 543, 566, 560, 639),
    ("14SERA1P58930", 440, 448, 467, 455, 498, 532, 556, 574, 582, 605, 599, 678),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 115,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 116 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 58cm
# ============================================

# Sobremódulo rincón lineal 1 puerta fondo 580 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERC1P58650", 286, 294, 307, 296, 314, 352, 372, 372, 388, 412, 424, 475),
    ("14SERC1P58700", 290, 300, 314, 304, 326, 358, 380, 380, 398, 420, 438, 482),
    ("14SERC1P58750", 303, 313, 329, 321, 344, 369, 390, 390, 408, 435, 451, 497),
    ("14SERC1P58800", 309, 317, 334, 330, 356, 379, 402, 403, 421, 444, 454, 504),
    ("14SERC1P58850", 321, 332, 350, 347, 375, 396, 421, 422, 442, 458, 468, 518),
    ("14SERC1P58950", 339, 349, 370, 373, 405, 413, 439, 441, 462, 481, 491, 541),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 1 puerta fondo 580",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 116,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERC2P581000", 344, 356, 377, 379, 408, 420, 444, 434, 466, 486, 494, 545),
    ("14SERC2P581100", 379, 392, 413, 415, 444, 456, 480, 470, 502, 522, 530, 581),
    ("14SERC2P581200", 415, 428, 448, 451, 480, 492, 516, 506, 538, 558, 566, 617),
    ("14SERC2P581300", 451, 464, 484, 487, 516, 528, 552, 542, 574, 594, 602, 653),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 116,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 1 puerta fondo 580mm (Derecha/)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SET1P58400", 207, 212, 227, 224, 243, 267, 284, 289, 303, 307, 322, 369),
    ("14SET1P58450", 212, 218, 234, 234, 254, 277, 297, 302, 318, 315, 326, 376),
    ("14SET1P58500", 218, 225, 243, 244, 267, 289, 310, 315, 332, 325, 335, 385),
    ("14SET1P58600", 230, 237, 257, 264, 292, 300, 322, 327, 345, 340, 350, 401),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 116,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SET2P58600", 286, 296, 319, 309, 335, 411, 444, 451, 477, 486, 506, 611),
    ("14SET2P58700", 303, 313, 338, 333, 364, 434, 469, 477, 505, 508, 542, 632),
    ("14SET2P58800", 321, 331, 358, 358, 392, 446, 480, 489, 516, 530, 561, 654),
    ("14SET2P58900", 420, 348, 378, 382, 421, 471, 509, 519, 549, 553, 574, 676),
    ("14SET2P581000", 354, 367, 398, 407, 450, 499, 540, 550, 583, 575, 595, 697),
    ("14SET2P581200", 387, 401, 437, 456, 507, 532, 576, 587, 621, 621, 640, 740),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 116,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 117 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 58cm
# ============================================

# Sobremódulo persiana aluminio fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEPER58P450", 620, 620, 620, 620, 620, 620, 620, 620, 620, 620, 620, 620),
    ("14SEPER58P600", 732, 732, 732, 732, 732, 732, 732, 732, 732, 732, 732, 732),
    ("14SEPER58P900", 1002, 1002, 1002, 1002, 1002, 1002, 1002, 1002, 1002, 1002, 1002, 1002),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo persiana aluminio fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 117,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 118 - SOBREMÓDULOS DE 147cm DECORATIVOS
# ============================================

# Sobremódulo Decorativo fondo 33cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEDEC300", 335, 387, 323, 287, 340, 425, 480, 425, 462, 443, 452, 443),
    ("14SEDEC350", 358, 408, 345, 308, 362, 447, 502, 447, 483, 465, 473, 465),
    ("14SEDEC400", 370, 427, 360, 317, 378, 482, 545, 482, 526, 505, 510, 505),
    ("14SEDEC450", 392, 447, 377, 333, 395, 510, 575, 510, 554, 532, 542, 532),
    ("14SEDEC500", 417, 473, 400, 355, 418, 537, 605, 537, 583, 562, 568, 562),
    ("14SEDEC600", 452, 512, 440, 392, 462, 583, 658, 583, 633, 607, 617, 607),
    ("14SEDEC700", 487, 547, 475, 427, 497, 618, 694, 618, 668, 642, 652, 642),
    ("14SEDEC800", 522, 582, 510, 462, 532, 653, 729, 653, 704, 677, 687, 677),
    ("14SEDEC900", 557, 617, 545, 497, 567, 689, 764, 689, 739, 712, 722, 712),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 33cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 147cm",
        "sourcePage": 118,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo Decorativo fondo 58cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEDEC58400", 444, 512, 432, 380, 454, 578, 654, 578, 630, 606, 612, 606),
    ("14SEDEC58450", 470, 536, 452, 400, 474, 612, 690, 612, 664, 638, 650, 638),
    ("14SEDEC58500", 500, 568, 480, 426, 502, 644, 726, 644, 700, 674, 682, 674),
    ("14SEDEC58600", 542, 614, 528, 470, 554, 700, 790, 700, 760, 728, 740, 728),
    ("14SEDEC58700", 584, 656, 570, 512, 596, 742, 832, 742, 802, 770, 782, 770),
    ("14SEDEC58800", 626, 698, 612, 554, 638, 784, 874, 784, 844, 812, 824, 812),
    ("14SEDEC58900", 668, 740, 654, 596, 680, 826, 916, 826, 886, 854, 866, 854),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 58cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 147cm",
        "sourcePage": 118,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# PAGE 119 is a cover page for "PROGRAMA ESTÁNDAR - MUEBLES BAJOS" - no products

# ============================================
# PROCESS ALL PRODUCTS
# ============================================

new_refs = []
updated_count = 0
created_count = 0

for product in products_to_add:
    ref = product["reference"]
    
    if ref not in valid_references:
        valid_references.append(ref)
        new_refs.append(ref)
    
    existing = db.products.find_one({"reference": ref})
    
    if existing:
        db.products.update_one(
            {"reference": ref},
            {"$set": product}
        )
        updated_count += 1
    else:
        db.products.insert_one(product)
        created_count += 1

# Save updated valid references
with open('/app/valid_references.json', 'w') as f:
    json.dump(sorted(valid_references), f, indent=2)

final_count = len(valid_references)
total_products = db.products.count_documents({})

print(f"\n{'='*50}")
print(f"RESUMEN - PÁGINAS 115-118")
print(f"(Página 119 es portada de MUEBLES BAJOS)")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias añadidas: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
print(f"{'='*50}")

if new_refs:
    print(f"\nNuevas referencias añadidas:")
    for ref in sorted(new_refs):
        print(f"  - {ref}")
