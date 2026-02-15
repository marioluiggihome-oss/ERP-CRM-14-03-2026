#!/usr/bin/env python3
"""
Process pages 110-114 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm
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
# PAGE 110 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 33cm
# ============================================

# Sobremódulo micro 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEM1P600", 197, 204, 225, 237, 266, 269, 292, 297, 316, 310, 316, 359),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 1 Puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 110,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo micro 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEM2P600", 236, 248, 272, 265, 293, 378, 414, 422, 450, 437, 450, 541),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 2 Puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 110,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo micro 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEM1V600", 267, 273, 293, 307, 420, 326, 349, 354, 373, 366, 372, 416),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 110,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 111 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 33cm
# ============================================

# Sobremódulo micro 2 Vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEM2V600", 357, 330, 354, 349, 377, 434, 469, 479, 507, 494, 507, 596),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 2 Vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 111,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERA2P630", 360, 371, 396, 381, 409, 482, 515, 524, 550, 552, 573, 678),
    ("14SERA2P730", 386, 399, 425, 410, 439, 518, 554, 563, 591, 594, 616, 729),
    ("14SERA2P830", 414, 427, 456, 440, 472, 557, 596, 606, 636, 639, 663, 785),
    ("14SERA2P930", 445, 460, 491, 472, 506, 600, 642, 652, 685, 688, 713, 846),
    ("14SERA2P1030", 479, 494, 528, 508, 545, 644, 689, 702, 736, 741, 768, 910),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 111,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERA1P630", 278, 287, 305, 294, 421, 370, 394, 413, 420, 443, 437, 517),
    ("14SERA1P730", 317, 325, 344, 333, 376, 409, 433, 452, 459, 482, 476, 555),
    ("14SERA1P830", 356, 364, 383, 371, 414, 448, 472, 491, 498, 521, 515, 594),
    ("14SERA1P930", 394, 403, 422, 410, 453, 486, 511, 529, 537, 560, 554, 633),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 111,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERC1P650", 238, 247, 260, 248, 267, 304, 325, 325, 340, 365, 376, 428),
    ("14SERC1P700", 243, 253, 267, 257, 279, 312, 333, 333, 350, 373, 391, 435),
    ("14SERC1P750", 256, 266, 281, 274, 297, 322, 343, 343, 360, 388, 404, 450),
    ("14SERC1P800", 261, 270, 287, 283, 309, 332, 355, 356, 373, 396, 406, 457),
    ("14SERC1P850", 274, 284, 303, 300, 327, 349, 373, 375, 395, 411, 421, 471),
    ("14SERC1P950", 291, 302, 323, 326, 358, 366, 392, 394, 415, 434, 444, 494),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 111,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 112 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 33cm
# ============================================

# Sobremódulo rincón lineal 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SERC2P1000", 300, 313, 334, 420, 365, 377, 401, 391, 423, 443, 451, 502),
    ("14SERC2P1100", 420, 349, 369, 372, 401, 413, 437, 427, 459, 479, 487, 538),
    ("14SERC2P1200", 372, 385, 405, 408, 437, 449, 473, 463, 495, 515, 523, 574),
    ("14SERC2P1300", 408, 421, 441, 444, 473, 484, 509, 499, 530, 551, 559, 610),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 112,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SET1P400", 171, 177, 191, 188, 207, 231, 249, 253, 267, 272, 286, 333),
    ("14SET1P450", 177, 183, 198, 198, 218, 241, 262, 266, 282, 280, 290, 341),
    ("14SET1P500", 183, 190, 207, 208, 231, 253, 275, 279, 296, 289, 299, 349),
    ("14SET1P600", 194, 201, 221, 229, 256, 264, 286, 292, 309, 305, 315, 365),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 112,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SET2P600", 302, 312, 335, 325, 351, 427, 460, 467, 493, 502, 522, 627),
    ("14SET2P700", 319, 329, 354, 349, 379, 450, 484, 493, 520, 523, 558, 648),
    ("14SET2P800", 420, 346, 374, 374, 408, 461, 496, 504, 532, 546, 576, 670),
    ("14SET2P900", 352, 364, 394, 398, 437, 487, 525, 535, 565, 569, 589, 691),
    ("14SET2P1000", 369, 382, 414, 423, 466, 515, 556, 566, 599, 591, 611, 713),
    ("14SET2P1200", 402, 417, 453, 471, 523, 548, 592, 602, 637, 637, 655, 756),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 112,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo persiana aluminio (Note: reference uses 12SEPER prefix)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEPER33P450", 585, 585, 585, 585, 585, 585, 585, 585, 585, 585, 585, 585),
    ("14SEPER33P600", 691, 691, 691, 691, 691, 691, 691, 691, 691, 691, 691, 691),
    ("14SEPER33P900", 957, 957, 957, 957, 957, 957, 957, 957, 957, 957, 957, 957),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo persiana aluminio",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 33cm",
        "sourcePage": 112,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 113 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS DE 147cm FONDO 58cm
# ============================================

# Sobremódulo 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE1P58400", 218, 227, 246, 239, 263, 286, 308, 313, 330, 350, 369, 434),
    ("14SE1P58450", 230, 237, 258, 255, 281, 301, 326, 332, 350, 363, 379, 446),
    ("14SE1P58500", 240, 250, 273, 271, 299, 318, 344, 351, 371, 377, 393, 460),
    ("14SE1P58600", 261, 271, 298, 301, 420, 344, 373, 380, 402, 405, 419, 486),
    ("14SE1P58650", 288, 297, 324, 328, 362, 371, 399, 406, 428, 432, 445, 512),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 113,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2P58600", 305, 319, 351, 331, 365, 443, 483, 492, 524, 554, 586, 722),
    ("14SE2P58700", 326, 341, 376, 359, 400, 465, 507, 518, 551, 582, 623, 750),
    ("14SE2P58800", 347, 362, 400, 389, 435, 481, 524, 534, 569, 609, 647, 776),
    ("14SE2P58900", 368, 384, 426, 420, 471, 512, 560, 572, 609, 636, 667, 801),
    ("14SE2P581000", 393, 410, 452, 445, 497, 538, 585, 597, 634, 662, 692, 826),
    ("14SE2P581200", 418, 435, 477, 470, 522, 563, 610, 623, 659, 687, 717, 852),
    ("14SE2P581300", 443, 460, 502, 496, 547, 588, 635, 648, 685, 712, 742, 877),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 113,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas plegables fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2PPL58700", 471, 481, 503, 496, 522, 576, 605, 612, 635, 632, 661, 735),
    ("14SE2PPL58800", 487, 496, 521, 517, 547, 585, 615, 622, 645, 651, 676, 752),
    ("14SE2PPL58900", 501, 511, 537, 537, 570, 608, 639, 648, 672, 670, 686, 770),
    ("14SE2PPL581000", 516, 528, 556, 558, 595, 631, 665, 674, 701, 689, 705, 789),
    ("14SE2PPL581200", 545, 557, 590, 601, 644, 658, 695, 704, 734, 726, 742, 824),
    ("14SE2PPL581300", 575, 587, 619, 630, 674, 688, 724, 734, 763, 756, 771, 853),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas plegables fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 113,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 1 Vitrina fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE1V58400", 265, 274, 293, 289, 311, 320, 342, 348, 364, 385, 404, 468),
    ("14SE1V58450", 277, 292, 313, 310, 420, 343, 366, 373, 392, 405, 420, 487),
    ("14SE1V58500", 293, 315, 337, 420, 365, 371, 396, 402, 423, 429, 444, 511),
    ("14SE1V58600", 318, 350, 377, 381, 415, 411, 439, 446, 468, 470, 485, 552),
    ("14SE1V58650", 349, 377, 393, 398, 426, 420, 444, 461, 484, 486, 513, 566),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 Vitrina fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 113,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 114 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 147cm FONDO 58cm
# ============================================

# Sobremódulo 2 vitrinas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2V58600", 413, 412, 443, 424, 459, 510, 549, 560, 591, 622, 653, 790),
    ("14SE2V58700", 438, 447, 483, 467, 508, 546, 588, 599, 632, 663, 704, 831),
    ("14SE2V58800", 463, 482, 520, 510, 557, 575, 618, 629, 664, 704, 741, 869),
    ("14SE2V58900", 489, 520, 562, 557, 608, 623, 670, 681, 719, 747, 776, 911),
    ("14SE2V581000", 515, 558, 604, 601, 658, 670, 721, 733, 774, 788, 818, 951),
    ("14SE2V581200", 565, 628, 681, 690, 758, 749, 806, 820, 865, 870, 899, 1032),
    ("14SE2V581300", 650, 722, 784, 793, 872, 861, 927, 943, 995, 1001, 1034, 1187),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 vitrinas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 114,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 Vitrinas plegables fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SE2VPL58700", 647, 659, 685, 677, 707, 771, 806, 814, 840, 838, 871, 958),
    ("14SE2VPL58800", 665, 677, 706, 702, 736, 782, 817, 825, 853, 860, 889, 979),
    ("14SE2VPL58900", 682, 695, 725, 725, 764, 808, 846, 856, 885, 882, 901, 1000),
    ("14SE2VPL581000", 700, 714, 747, 750, 793, 836, 876, 886, 918, 904, 924, 1022),
    ("14SE2VPL581200", 735, 749, 788, 800, 851, 868, 911, 922, 957, 949, 967, 1064),
    ("14SE2VPL581300", 770, 783, 822, 835, 886, 903, 946, 957, 992, 983, 1001, 1098),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 Vitrinas plegables fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 114,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEH1P600", 194, 200, 214, 218, 238, 245, 260, 265, 278, 275, 281, 318),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 1 Puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 114,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo horno 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("14SEH2P600", 222, 229, 247, 237, 257, 311, 335, 340, 359, 361, 377, 453),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo horno 2 Puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 147cm FONDO 58cm",
        "sourcePage": 114,
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
print(f"RESUMEN - PÁGINAS 110-114")
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
