#!/usr/bin/env python3
"""
Process pages 105-109 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm/147cm
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
# PAGE 105 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 58cm
# ============================================

# Sobremódulo rincón angular 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERA1P58630", 273, 282, 300, 289, 331, 364, 388, 406, 413, 436, 430, 508),
    ("12SERA1P58730", 311, 320, 338, 327, 369, 402, 426, 444, 451, 474, 468, 546),
    ("12SERA1P58830", 349, 358, 376, 365, 407, 440, 464, 482, 489, 512, 506, 584),
    ("12SERA1P58930", 388, 396, 414, 403, 446, 478, 502, 520, 527, 550, 544, 622),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 105,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 1 puerta fondo 580 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERC1P58650", 234, 243, 255, 244, 262, 299, 319, 319, 335, 359, 370, 421),
    ("12SERC1P58700", 238, 248, 262, 253, 274, 306, 327, 327, 344, 367, 384, 428),
    ("12SERC1P58750", 251, 261, 277, 270, 292, 316, 337, 337, 354, 381, 397, 442),
    ("12SERC1P58800", 257, 265, 282, 278, 303, 326, 349, 350, 367, 390, 400, 449),
    ("12SERC1P58850", 270, 279, 298, 295, 322, 343, 367, 368, 388, 404, 414, 463),
    ("12SERC1P58950", 286, 296, 318, 320, 351, 360, 385, 387, 408, 426, 436, 486),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 1 puerta fondo 580",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 105,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERC2P581000", 295, 308, 328, 331, 359, 370, 394, 384, 415, 435, 444, 493),
    ("12SERC2P581100", 331, 343, 363, 366, 394, 406, 430, 420, 451, 471, 479, 528),
    ("12SERC2P581200", 366, 379, 398, 401, 430, 441, 465, 455, 486, 506, 514, 564),
    ("12SERC2P581300", 401, 414, 434, 437, 465, 476, 500, 490, 521, 541, 550, 599),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 105,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 106 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 58cm
# ============================================

# Sobremódulo termo 1 puerta fondo 580mm (Derecha/)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SET1P58400", 166, 171, 186, 188, 208, 226, 244, 248, 261, 270, 276, 321),
    ("12SET1P58450", 175, 181, 197, 202, 224, 243, 263, 268, 284, 281, 288, 332),
    ("12SET1P58500", 185, 191, 209, 216, 239, 267, 290, 296, 314, 293, 299, 343),
    ("12SET1P58600", 204, 211, 231, 244, 272, 275, 298, 305, 322, 317, 322, 366),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 106,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SET2P58600", 237, 248, 273, 265, 294, 378, 414, 422, 450, 437, 450, 541),
    ("12SET2P58700", 255, 268, 294, 292, 326, 386, 422, 431, 459, 461, 474, 564),
    ("12SET2P58800", 275, 287, 316, 320, 359, 395, 431, 439, 467, 484, 497, 586),
    ("12SET2P58900", 296, 308, 339, 350, 393, 432, 471, 481, 513, 509, 522, 610),
    ("12SET2P581000", 315, 329, 363, 377, 425, 480, 526, 538, 574, 532, 545, 632),
    ("12SET2P581200", 353, 366, 407, 433, 490, 497, 543, 554, 590, 579, 590, 677),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 106,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo persiana aluminio fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEPER58P450", 609, 609, 609, 609, 609, 609, 609, 609, 609, 609, 609, 609),
    ("12SEPER58P600", 716, 716, 716, 716, 716, 716, 716, 716, 716, 716, 716, 716),
    ("12SEPER58P900", 985, 985, 985, 985, 985, 985, 985, 985, 985, 985, 985, 985),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo persiana aluminio fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 106,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 107 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS DE 127cm DECORATIVOS
# ============================================

# Sobremódulo Decorativo fondo 33cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEDEC300", 291, 420, 281, 249, 296, 370, 417, 370, 402, 386, 393, 386),
    ("12SEDEC350", 312, 355, 300, 268, 315, 389, 436, 389, 420, 404, 412, 404),
    ("12SEDEC400", 322, 371, 313, 275, 329, 419, 474, 419, 457, 439, 444, 439),
    ("12SEDEC450", 341, 389, 328, 290, 344, 444, 500, 444, 481, 462, 471, 462),
    ("12SEDEC500", 362, 412, 348, 309, 364, 467, 526, 467, 507, 489, 494, 489),
    ("12SEDEC600", 393, 445, 383, 341, 402, 507, 573, 507, 551, 528, 536, 528),
    ("12SEDEC700", 423, 475, 413, 371, 432, 538, 603, 538, 581, 558, 567, 558),
    ("12SEDEC800", 454, 506, 444, 402, 462, 568, 633, 568, 612, 589, 597, 589),
    ("12SEDEC900", 484, 536, 474, 432, 493, 599, 664, 599, 642, 619, 628, 619),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 33cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 127cm",
        "sourcePage": 107,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo Decorativo fondo 58cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEDEC58400", 386, 445, 376, 331, 395, 503, 569, 503, 548, 527, 532, 527),
    ("12SEDEC58450", 409, 466, 393, 348, 412, 532, 600, 532, 578, 555, 565, 555),
    ("12SEDEC58500", 435, 494, 417, 371, 437, 560, 631, 560, 609, 586, 593, 586),
    ("12SEDEC58600", 471, 534, 459, 409, 482, 609, 687, 609, 661, 633, 644, 633),
    ("12SEDEC58700", 508, 571, 496, 445, 518, 645, 724, 645, 698, 670, 680, 670),
    ("12SEDEC58800", 544, 607, 532, 482, 555, 682, 760, 682, 734, 706, 717, 706),
    ("12SEDEC58900", 581, 644, 569, 518, 591, 718, 797, 718, 771, 743, 753, 743),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 58cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 127cm",
        "sourcePage": 107,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 108 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS DE 147cm FONDO 33cm
# ============================================

# Sobremódulo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE1P400", 171, 180, 198, 192, 215, 238, 260, 266, 282, 302, 321, 386),
    ("14SE1P450", 183, 190, 211, 208, 234, 254, 278, 285, 302, 316, 332, 399),
    ("14SE1P500", 193, 203, 226, 224, 252, 271, 297, 303, 323, 330, 345, 413),
    ("14SE1P600", 214, 224, 251, 254, 289, 297, 326, 333, 355, 358, 372, 439),
    ("14SE1P650", 240, 250, 277, 280, 315, 323, 352, 359, 381, 384, 398, 465),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 108,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2P600", 258, 273, 305, 285, 319, 397, 437, 446, 478, 508, 540, 676),
    ("14SE2P700", 279, 295, 330, 313, 354, 419, 461, 471, 505, 536, 576, 704),
    ("14SE2P800", 300, 316, 354, 342, 389, 435, 478, 488, 523, 563, 601, 730),
    ("14SE2P900", 321, 338, 380, 374, 425, 466, 513, 526, 563, 590, 621, 755),
    ("14SE2P1000", 347, 363, 405, 399, 450, 491, 539, 551, 588, 615, 646, 780),
    ("14SE2P1200", 372, 389, 431, 424, 476, 517, 564, 576, 613, 641, 671, 805),
    ("14SE2P1300", 397, 414, 456, 449, 501, 542, 589, 602, 638, 666, 696, 831),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 108,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas plegables (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2PPL700", 420, 429, 452, 445, 470, 524, 554, 561, 583, 581, 609, 683),
    ("14SE2PPL800", 435, 445, 469, 466, 495, 534, 563, 570, 594, 600, 624, 701),
    ("14SE2PPL900", 449, 460, 486, 486, 519, 556, 588, 596, 621, 619, 635, 719),
    ("14SE2PPL1000", 465, 476, 505, 507, 543, 580, 614, 622, 649, 637, 654, 737),
    ("14SE2PPL1200", 494, 506, 539, 549, 593, 607, 643, 653, 682, 675, 690, 773),
    ("14SE2PPL1300", 523, 535, 568, 579, 622, 636, 673, 682, 711, 704, 720, 802),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas plegables",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 108,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 109 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 33cm
# ============================================

# Sobremódulo 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE1V400", 261, 244, 263, 258, 280, 290, 312, 317, 334, 355, 374, 438),
    ("14SE1V450", 274, 261, 282, 279, 306, 313, 420, 342, 361, 375, 390, 457),
    ("14SE1V500", 289, 279, 302, 301, 330, 420, 361, 368, 387, 395, 410, 477),
    ("14SE1V600", 317, 314, 340, 344, 379, 375, 403, 410, 433, 435, 449, 516),
    ("14SE1V650", 348, 344, 371, 375, 410, 405, 434, 440, 463, 465, 480, 546),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 109,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2V600", 426, 376, 407, 389, 423, 474, 513, 524, 555, 586, 617, 754),
    ("14SE2V700", 454, 411, 445, 431, 471, 509, 551, 562, 595, 626, 667, 794),
    ("14SE2V800", 481, 444, 483, 474, 519, 538, 581, 592, 626, 667, 705, 833),
    ("14SE2V900", 506, 480, 522, 517, 568, 583, 630, 642, 679, 707, 736, 872),
    ("14SE2V1000", 542, 513, 558, 553, 608, 624, 674, 686, 727, 756, 788, 893),
    ("14SE2V1200", 579, 549, 597, 591, 650, 667, 721, 735, 778, 809, 843, 956),
    ("14SE2V1300", 620, 588, 639, 633, 696, 714, 772, 786, 832, 866, 902, 902),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 109,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 Vitrinas plegables (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2VPL700", 602, 613, 640, 631, 662, 726, 760, 769, 795, 792, 826, 913),
    ("14SE2VPL800", 620, 631, 661, 656, 691, 737, 772, 780, 808, 815, 844, 934),
    ("14SE2VPL900", 637, 649, 680, 680, 719, 763, 801, 810, 840, 837, 856, 955),
    ("14SE2VPL1000", 655, 669, 702, 705, 748, 791, 831, 841, 873, 859, 878, 977),
    ("14SE2VPL1200", 690, 704, 742, 755, 806, 823, 866, 877, 912, 903, 921, 1019),
    ("14SE2VPL1300", 724, 738, 777, 790, 841, 858, 901, 912, 946, 938, 956, 1053),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 Vitrinas plegables",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 109,
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
print(f"RESUMEN - PÁGINAS 105-109")
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
