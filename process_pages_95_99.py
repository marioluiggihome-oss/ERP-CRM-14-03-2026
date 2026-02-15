#!/usr/bin/env python3
"""
Process pages 95-99 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 110cm/127cm
"""

import json
import os
from pymongo import MongoClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
# Remove quotes if present
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

# All products from pages 95-99
products_to_add = []

# ============================================
# PAGE 95 - PROGRAMA ESTÁNDAR - SOBREMÓDULOS - ALTO 110cm FONDO 58cm
# ============================================

# Sobremódulo rincón lineal 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMRC1P58650", 191, 199, 211, 200, 218, 253, 272, 272, 286, 309, 320, 369),
    ("11SMRC1P58700", 195, 204, 218, 208, 228, 259, 280, 280, 296, 318, 334, 376),
    ("11SMRC1P58750", 207, 216, 231, 224, 246, 269, 289, 289, 305, 331, 346, 389),
    ("11SMRC1P58800", 212, 220, 236, 232, 257, 278, 300, 301, 318, 339, 349, 396),
    ("11SMRC1P58850", 224, 234, 251, 249, 274, 295, 318, 319, 338, 353, 362, 409),
    ("11SMRC1P58950", 241, 250, 270, 273, 303, 311, 335, 420, 357, 374, 384, 431),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 110cm",
        "sourcePage": 95,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón lineal 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMRC2P581000", 243, 255, 274, 277, 304, 315, 338, 328, 358, 377, 385, 432),
    ("11SMRC2P581100", 277, 289, 308, 311, 338, 349, 372, 362, 392, 411, 419, 466),
    ("11SMRC2P581200", 311, 323, 342, 345, 372, 382, 405, 396, 426, 445, 453, 500),
    ("11SMRC2P581300", 345, 357, 376, 378, 405, 416, 439, 430, 459, 478, 486, 534),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón lineal 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 110cm",
        "sourcePage": 95,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 1 puerta fondo 580mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMT1P58400", 137, 142, 154, 151, 166, 186, 200, 203, 215, 218, 230, 268),
    ("11SMT1P58450", 142, 147, 159, 159, 176, 194, 210, 214, 226, 225, 233, 274),
    ("11SMT1P58500", 147, 152, 166, 167, 186, 203, 221, 224, 238, 232, 240, 281),
    ("11SMT1P58600", 156, 162, 178, 184, 206, 213, 230, 234, 248, 245, 253, 293),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 1 puerta fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 110cm",
        "sourcePage": 95,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo termo 2 puertas fondo 580mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMT2P58600", 213, 223, 242, 232, 254, 316, 344, 350, 372, 375, 392, 480),
    ("11SMT2P58700", 228, 238, 261, 253, 280, 335, 366, 373, 396, 393, 422, 498),
    ("11SMT2P58800", 244, 253, 279, 275, 305, 345, 375, 382, 407, 413, 438, 516),
    ("11SMT2P58900", 258, 269, 296, 296, 329, 368, 401, 409, 434, 432, 449, 535),
    ("11SMT2P581000", 274, 286, 315, 317, 355, 392, 427, 436, 463, 451, 468, 554),
    ("11SMT2P581200", 304, 316, 350, 361, 405, 420, 457, 467, 497, 490, 506, 590),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo termo 2 puertas fondo 580mm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 110cm",
        "sourcePage": 95,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 96 - SOBREMÓDULOS DE 110cm DECORATIVOS
# ============================================

# Sobremódulo Decorativo fondo 33cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMDEC300", 249, 287, 240, 213, 253, 316, 357, 316, 343, 330, 336, 330),
    ("11SMDEC350", 266, 304, 256, 229, 269, 332, 373, 332, 359, 346, 352, 346),
    ("11SMDEC400", 275, 317, 268, 235, 281, 358, 405, 358, 390, 375, 379, 375),
    ("11SMDEC450", 291, 332, 280, 248, 294, 379, 427, 379, 411, 395, 403, 395),
    ("11SMDEC500", 310, 352, 297, 264, 311, 399, 450, 399, 434, 418, 422, 418),
    ("11SMDEC600", 336, 380, 327, 291, 343, 434, 489, 434, 471, 451, 458, 451),
    ("11SMDEC700", 362, 406, 353, 317, 369, 460, 515, 460, 497, 477, 484, 477),
    ("11SMDEC800", 388, 432, 379, 343, 395, 486, 541, 486, 523, 503, 510, 503),
    ("11SMDEC900", 414, 458, 405, 369, 421, 512, 567, 512, 549, 529, 536, 529),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 33cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 110cm",
        "sourcePage": 96,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo Decorativo fondo 58cm (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("11SMDEC58400", 330, 381, 321, 282, 338, 430, 486, 430, 468, 451, 455, 451),
    ("11SMDEC58450", 349, 398, 420, 297, 352, 455, 513, 455, 494, 474, 483, 474),
    ("11SMDEC58500", 372, 422, 357, 317, 373, 479, 540, 479, 520, 501, 507, 501),
    ("11SMDEC58600", 403, 456, 393, 349, 412, 520, 587, 520, 565, 541, 550, 541),
    ("11SMDEC58700", 434, 488, 424, 381, 443, 552, 619, 552, 596, 572, 581, 572),
    ("11SMDEC58800", 465, 519, 455, 412, 474, 583, 650, 583, 627, 604, 613, 604),
    ("11SMDEC58900", 497, 550, 486, 443, 506, 614, 681, 614, 659, 635, 644, 635),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo Decorativo fondo 58cm",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "DECORATIVOS 110cm",
        "sourcePage": 96,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 97 - SOBREMÓDULOS DE 127cm FONDO 33cm
# ============================================

# Sobremódulo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE1P400", 146, 151, 166, 168, 188, 206, 224, 228, 242, 250, 256, 301),
    ("12SE1P450", 154, 160, 176, 182, 203, 222, 243, 247, 263, 260, 267, 311),
    ("12SE1P500", 163, 169, 187, 194, 218, 245, 269, 274, 292, 272, 277, 321),
    ("12SE1P600", 180, 187, 207, 219, 248, 251, 274, 280, 298, 293, 298, 342),
    ("12SE1P650", 202, 209, 229, 242, 270, 273, 296, 302, 320, 315, 320, 364),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 97,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2P600", 218, 231, 255, 247, 276, 360, 396, 404, 433, 420, 433, 523),
    ("12SE2P700", 236, 248, 275, 273, 306, 366, 402, 411, 439, 441, 454, 544),
    ("12SE2P800", 253, 265, 294, 298, 337, 373, 408, 417, 445, 462, 475, 564),
    ("12SE2P900", 270, 281, 314, 324, 368, 405, 446, 456, 487, 483, 496, 584),
    ("12SE2P1000", 294, 306, 338, 349, 392, 429, 470, 480, 511, 507, 520, 608),
    ("12SE2P1200", 318, 330, 362, 373, 416, 454, 495, 504, 536, 531, 544, 632),
    ("12SE2P1300", 342, 354, 386, 397, 440, 478, 519, 528, 560, 555, 568, 656),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 97,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 puertas plegables (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2PPL700", 419, 428, 450, 443, 469, 523, 553, 560, 582, 580, 608, 682),
    ("12SE2PPL800", 434, 443, 468, 465, 494, 533, 562, 569, 593, 599, 623, 700),
    ("12SE2PPL900", 448, 459, 485, 485, 517, 555, 587, 595, 620, 617, 634, 717),
    ("12SE2PPL1000", 463, 475, 503, 506, 542, 579, 613, 621, 648, 636, 653, 736),
    ("12SE2PPL1200", 493, 505, 537, 548, 592, 606, 642, 652, 681, 674, 689, 771),
    ("12SE2PPL1300", 522, 534, 567, 577, 621, 635, 671, 681, 710, 703, 719, 801),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 puertas plegables",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 97,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 98 - SOBREMÓDULOS DE 127cm FONDO 33cm (cont.)
# ============================================

# Sobremódulo 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE1V400", 216, 209, 224, 227, 246, 250, 268, 272, 287, 295, 301, 345),
    ("12SE1V450", 226, 223, 239, 245, 267, 272, 292, 297, 313, 311, 317, 361),
    ("12SE1V500", 236, 238, 255, 264, 288, 301, 324, 330, 348, 328, 333, 377),
    ("12SE1V600", 258, 266, 287, 300, 329, 318, 341, 347, 365, 359, 365, 408),
    ("12SE1V650", 287, 294, 315, 329, 357, 347, 370, 375, 394, 387, 394, 437),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 98,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2V600", 351, 323, 348, 341, 370, 427, 463, 471, 500, 486, 500, 590),
    ("12SE2V700", 370, 352, 378, 378, 412, 444, 480, 489, 518, 519, 532, 622),
    ("12SE2V800", 394, 379, 410, 415, 454, 462, 498, 506, 534, 551, 564, 653),
    ("12SE2V900", 413, 407, 440, 452, 495, 506, 546, 555, 588, 584, 596, 685),
    ("12SE2V1000", 441, 436, 468, 480, 523, 534, 574, 584, 616, 612, 625, 713),
    ("12SE2V1200", 469, 464, 497, 508, 551, 563, 603, 612, 645, 641, 653, 741),
    ("12SE2V1300", 498, 492, 525, 537, 580, 591, 631, 641, 673, 669, 681, 770),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 98,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo 2 Vitrinas plegables (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SE2VPL700", 510, 520, 542, 535, 561, 615, 644, 652, 674, 671, 700, 774),
    ("12SE2VPL800", 526, 535, 560, 556, 586, 624, 654, 661, 684, 690, 715, 791),
    ("12SE2VPL900", 540, 550, 576, 576, 609, 647, 679, 687, 711, 709, 726, 809),
    ("12SE2VPL1000", 555, 567, 595, 597, 634, 670, 704, 713, 740, 728, 744, 828),
    ("12SE2VPL1200", 584, 596, 629, 640, 683, 697, 734, 743, 773, 766, 781, 863),
    ("12SE2VPL1300", 614, 626, 659, 669, 713, 727, 763, 773, 802, 795, 810, 893),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo 2 Vitrinas plegables",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 98,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo micro 1 Puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEM1P600", 154, 160, 174, 180, 198, 205, 222, 226, 238, 235, 243, 279),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 1 Puerta",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 98,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 99 - SOBREMÓDULOS ALTO 127cm FONDO 33cm (cont.)
# ============================================

# Sobremódulo micro 2 Puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEM2P600", 182, 190, 208, 197, 217, 271, 295, 301, 320, 322, 337, 414),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 2 Puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 99,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo micro 1 Vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEM1V600", 218, 218, 233, 238, 258, 251, 268, 271, 285, 281, 288, 326),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 1 Vitrina",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 99,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo micro 2 Vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SEM2V600", 285, 261, 278, 271, 291, 317, 341, 347, 365, 369, 383, 460),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo micro 2 Vitrinas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 99,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Sobremódulo rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("12SERA2P630", 308, 317, 338, 326, 349, 412, 440, 448, 470, 472, 489, 579),
    ("12SERA2P730", 330, 341, 363, 351, 375, 443, 473, 481, 505, 508, 526, 623),
    ("12SERA2P830", 354, 365, 390, 376, 403, 476, 509, 518, 543, 546, 567, 671),
    ("12SERA2P930", 380, 394, 419, 403, 433, 513, 548, 557, 585, 588, 610, 723),
    ("12SERA2P1030", 410, 422, 451, 434, 466, 551, 589, 600, 629, 633, 656, 778),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Sobremódulo rincón angular 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "SOBREMÓDULOS",
        "series": "ALTO 127cm FONDO 33cm",
        "sourcePage": 99,
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
    
    # Add to valid references if not already there
    if ref not in valid_references:
        valid_references.append(ref)
        new_refs.append(ref)
    
    # Check if product exists in database
    existing = db.products.find_one({"reference": ref})
    
    if existing:
        # Update existing product
        db.products.update_one(
            {"reference": ref},
            {"$set": product}
        )
        updated_count += 1
    else:
        # Create new product
        db.products.insert_one(product)
        created_count += 1

# Save updated valid references
with open('/app/valid_references.json', 'w') as f:
    json.dump(sorted(valid_references), f, indent=2)

final_count = len(valid_references)
total_products = db.products.count_documents({})

print(f"\n{'='*50}")
print(f"RESUMEN - PÁGINAS 95-99")
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
