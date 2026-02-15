#!/usr/bin/env python3
"""
Process pages 100-104 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm
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
# PAGE 100 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 33cm
# ============================================

# Sobremódulo rincón angular 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERA1P630", 238, 245, 261, 251, 288, 316, 337, 353, 359, 379, 374, 441),
    ("12SERA1P730", 271, 278, 294, 284, 321, 349, 370, 386, 392, 412, 407, 475),
    ("12SERA1P830", 304, 311, 327, 317, 354, 383, 403, 419, 426, 445, 440, 508),
    ("12SERA1P930", 337, 344, 360, 351, 387, 416, 437, 453, 459, 478, 473, 541),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 100,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERC1P650", 204, 211, 222, 212, 228, 260, 277, 277, 291, 312, 322, 366),
    ("12SERC1P700", 207, 216, 228, 220, 238, 266, 285, 285, 299, 319, 334, 372),
    ("12SERC1P750", 218, 227, 241, 234, 254, 275, 293, 293, 308, 331, 345, 384),
    ("12SERC1P800", 223, 231, 245, 242, 264, 284, 303, 304, 319, 339, 347, 390),
    ("12SERC1P850", 234, 243, 259, 256, 280, 298, 319, 320, 338, 351, 360, 403),
    ("12SERC1P950", 249, 258, 276, 279, 306, 313, 335, 420, 355, 371, 379, 422),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 100,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERC2P1000", 257, 268, 285, 288, 312, 322, 343, 334, 361, 378, 386, 429),
    ("12SERC2P1100", 288, 299, 316, 318, 343, 353, 374, 365, 392, 409, 417, 460),
    ("12SERC2P1200", 318, 329, 347, 349, 374, 383, 404, 396, 423, 440, 447, 490),
    ("12SERC2P1300", 349, 360, 377, 380, 404, 414, 435, 426, 453, 471, 478, 521),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 100,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Alto termo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SET1P400", 145, 150, 162, 160, 175, 196, 211, 214, 227, 230, 242, 283),
    ("12SET1P450", 150, 155, 168, 168, 185, 205, 222, 225, 239, 238, 246, 289),
    ("12SET1P500", 155, 161, 175, 177, 196, 214, 233, 236, 251, 245, 253, 296),
    ("12SET1P600", 164, 171, 188, 194, 217, 224, 242, 247, 262, 258, 267, 309),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Alto termo 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 100,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 101 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 33cm
# ============================================

# Sobremódulo termo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SET2P600", 198, 211, 235, 227, 256, 340, 376, 384, 413, 400, 413, 503),
    ("12SET2P700", 216, 228, 255, 253, 286, 347, 382, 391, 419, 421, 434, 524),
    ("12SET2P800", 233, 245, 274, 278, 317, 353, 389, 397, 425, 442, 455, 544),
    ("12SET2P900", 250, 261, 294, 305, 348, 385, 426, 436, 467, 463, 476, 564),
    ("12SET2P1000", 274, 286, 318, 329, 372, 410, 450, 460, 491, 487, 500, 588),
    ("12SET2P1200", 298, 310, 342, 353, 396, 434, 475, 484, 516, 511, 524, 612),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 101,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo persiana aluminio
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEPER33P450", 574, 574, 574, 574, 574, 574, 574, 574, 574, 574, 574, 574),
    ("12SEPER33P600", 678, 678, 678, 678, 678, 678, 678, 678, 678, 678, 678, 678),
    ("12SEPER33P900", 941, 941, 941, 941, 941, 941, 941, 941, 941, 941, 941, 941),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo persiana aluminio",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 101,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 102 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 58cm
# ============================================

# Sobremódulo 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE1P58400", 179, 184, 198, 201, 221, 238, 256, 260, 274, 282, 289, 334),
    ("12SE1P58450", 188, 193, 210, 214, 236, 255, 275, 280, 296, 294, 300, 344),
    ("12SE1P58500", 197, 204, 222, 229, 252, 279, 302, 309, 327, 306, 312, 356),
    ("12SE1P58600", 216, 224, 244, 256, 285, 288, 311, 317, 335, 330, 335, 379),
    ("12SE1P58650", 235, 243, 263, 275, 303, 307, 330, 420, 354, 349, 354, 398),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 102,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2P58600", 256, 267, 292, 284, 313, 397, 433, 441, 469, 456, 469, 560),
    ("12SE2P58700", 274, 287, 313, 311, 344, 405, 441, 449, 478, 480, 492, 583),
    ("12SE2P58800", 294, 306, 335, 339, 378, 414, 449, 458, 486, 503, 516, 605),
    ("12SE2P58900", 315, 327, 358, 369, 412, 450, 490, 500, 532, 528, 541, 629),
    ("12SE2P581000", 334, 348, 382, 396, 444, 499, 545, 557, 593, 551, 564, 651),
    ("12SE2P581200", 372, 385, 426, 452, 509, 516, 562, 573, 609, 597, 609, 696),
    ("12SE2P581300", 402, 416, 457, 482, 540, 546, 592, 604, 639, 628, 639, 727),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 102,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas plegables fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2PPL58700", 464, 473, 496, 489, 514, 568, 598, 605, 627, 625, 653, 727),
    ("12SE2PPL58800", 479, 489, 513, 510, 539, 578, 607, 614, 638, 644, 668, 745),
    ("12SE2PPL58900", 493, 504, 530, 530, 563, 600, 632, 640, 665, 663, 679, 763),
    ("12SE2PPL581000", 508, 520, 548, 551, 587, 624, 658, 666, 693, 681, 698, 781),
    ("12SE2PPL581200", 538, 550, 583, 593, 637, 651, 687, 697, 726, 719, 734, 817),
    ("12SE2PPL581300", 567, 579, 612, 623, 666, 680, 717, 726, 755, 748, 764, 846),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas plegables fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 102,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 103 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 58cm
# ============================================

# Sobremódulo 1 Vitrina fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE1V58400", 248, 253, 268, 270, 290, 308, 326, 330, 343, 352, 358, 403),
    ("12SE1V58450", 257, 263, 279, 284, 306, 324, 344, 350, 365, 363, 370, 414),
    ("12SE1V58500", 267, 273, 291, 298, 321, 349, 372, 378, 396, 375, 381, 425),
    ("12SE1V58600", 286, 293, 313, 326, 354, 357, 380, 386, 404, 399, 404, 448),
    ("12SE1V58650", 305, 312, 332, 344, 373, 376, 399, 405, 423, 418, 423, 467),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 Vitrina fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 103,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 vitrinas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2V58600", 369, 376, 396, 408, 437, 440, 463, 469, 487, 482, 487, 531),
    ("12SE2V58700", 389, 404, 432, 422, 456, 555, 596, 606, 639, 625, 639, 745),
    ("12SE2V58800", 410, 423, 455, 453, 491, 562, 604, 614, 647, 649, 664, 770),
    ("12SE2V58900", 429, 443, 477, 482, 528, 569, 611, 621, 654, 674, 689, 793),
    ("12SE2V581000", 449, 463, 501, 513, 563, 608, 655, 667, 703, 698, 713, 816),
    ("12SE2V581200", 477, 491, 529, 541, 592, 636, 684, 695, 732, 727, 741, 845),
    ("12SE2V581300", 506, 519, 557, 569, 620, 664, 712, 723, 760, 755, 770, 873),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 vitrinas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 103,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 Vitrinas plegables fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2VPL58700", 567, 576, 599, 592, 618, 672, 701, 708, 731, 728, 756, 831),
    ("12SE2VPL58800", 582, 592, 616, 613, 642, 681, 711, 718, 741, 747, 772, 848),
    ("12SE2VPL58900", 596, 607, 633, 633, 666, 704, 840, 743, 768, 766, 782, 866),
    ("12SE2VPL581000", 612, 624, 652, 654, 691, 727, 761, 769, 796, 785, 801, 885),
    ("12SE2VPL581200", 641, 653, 686, 696, 740, 754, 791, 800, 829, 822, 838, 920),
    ("12SE2VPL581300", 671, 682, 715, 726, 769, 783, 820, 829, 859, 852, 867, 949),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 Vitrinas plegables fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 103,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEH1P600", 171, 175, 187, 186, 201, 204, 215, 218, 228, 233, 242, 271),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 1 Puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 103,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 104 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 127cm FONDO 58cm
# ============================================

# Sobremódulo horno 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEH2P600", 196, 203, 217, 207, 223, 246, 261, 266, 278, 307, 322, 383),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 2 Puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 104,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEH1V600", 227, 218, 231, 230, 245, 238, 251, 253, 263, 269, 276, 306),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 104,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 2 Vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEH2V600", 286, 254, 269, 259, 274, 281, 297, 301, 314, 342, 358, 419),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 2 Vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 104,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERA2P58630", 354, 365, 389, 375, 402, 474, 506, 515, 540, 543, 563, 666),
    ("12SERA2P58730", 379, 392, 417, 403, 431, 509, 544, 553, 581, 584, 605, 717),
    ("12SERA2P58830", 407, 420, 448, 433, 464, 547, 585, 595, 625, 628, 652, 772),
    ("12SERA2P58930", 437, 453, 482, 464, 498, 590, 631, 641, 673, 676, 701, 831),
    ("12SERA2P581030", 471, 485, 519, 499, 536, 633, 677, 690, 724, 728, 755, 895),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 58cm",
        "sourcePage": 104,
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
print(f"RESUMEN - PÁGINAS 100-104")
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
