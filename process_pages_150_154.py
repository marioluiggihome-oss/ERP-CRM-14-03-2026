#!/usr/bin/env python3
"""
Process pages 150-154 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS 80cm FONDO ESTÁNDAR (continuación)
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
# PAGE 150 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 2 caceroleros 320mm + 1 cajón 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2G1CB300", 223, 223, 233, 238, 253, 284, 300, 303, 317, 357, 374, 423),
    ("8B2G1CB350", 232, 233, 245, 249, 266, 294, 312, 316, 329, 376, 394, 448),
    ("8B2G1CB400", 242, 244, 256, 260, 278, 299, 317, 321, 335, 382, 400, 455),
    ("8B2G1CB450", 252, 254, 269, 273, 292, 313, 332, 420, 351, 402, 420, 480),
    ("8B2G1CB500", 261, 265, 280, 286, 307, 318, 337, 341, 356, 408, 426, 486),
    ("8B2G1CB600", 281, 286, 305, 310, 334, 329, 348, 352, 366, 421, 439, 499),
    ("8B2G1CB700", 302, 310, 331, 334, 362, 363, 386, 392, 408, 539, 583, 649),
    ("8B2G1CB800", 323, 331, 354, 361, 393, 412, 440, 447, 469, 558, 595, 668),
    ("8B2G1CB900", 345, 353, 379, 385, 420, 460, 494, 502, 528, 576, 610, 687),
    ("8B2G1CB1000", 387, 397, 432, 421, 462, 534, 579, 589, 624, 634, 652, 738),
    ("8B2G1CB1200", 414, 423, 459, 446, 488, 555, 600, 610, 645, 659, 677, 763),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 320mm + 1 cajón 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 150, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 320mm + 1 cajón 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2G1CL300", 333, 334, 344, 350, 364, 395, 411, 415, 427, 468, 484, 534),
    ("8B2G1CL350", 343, 344, 356, 360, 376, 405, 422, 426, 440, 487, 504, 560),
    ("8B2G1CL400", 353, 354, 368, 372, 390, 411, 427, 432, 445, 494, 510, 565),
    ("8B2G1CL450", 363, 365, 379, 384, 403, 424, 442, 447, 461, 512, 531, 590),
    ("8B2G1CL500", 373, 376, 392, 396, 417, 429, 447, 452, 466, 519, 538, 596),
    ("8B2G1CL600", 393, 397, 415, 421, 445, 440, 458, 463, 478, 531, 550, 609),
    ("8B2G1CL700", 414, 420, 441, 445, 473, 475, 497, 502, 520, 650, 694, 760),
    ("8B2G1CL800", 435, 441, 465, 471, 503, 523, 550, 558, 580, 668, 706, 778),
    ("8B2G1CL900", 456, 463, 490, 496, 531, 570, 604, 612, 638, 687, 720, 798),
    ("8B2G1CL1000", 498, 507, 542, 531, 572, 645, 689, 699, 734, 744, 762, 848),
    ("8B2G1CL1200", 524, 533, 569, 557, 599, 666, 710, 720, 755, 770, 788, 874),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 320mm + 1 cajón 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 150, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 151 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 cacerolero 400mm + 2 cajones 200mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G2CB300", 210, 214, 226, 236, 254, 289, 308, 313, 328, 382, 402, 480),
    ("8B1G2CB350", 223, 231, 246, 249, 268, 306, 327, 332, 349, 405, 427, 511),
    ("8B1G2CB400", 233, 243, 258, 263, 284, 313, 334, 339, 356, 415, 437, 521),
    ("8B1G2CB450", 244, 254, 271, 277, 300, 322, 344, 350, 368, 437, 460, 548),
    ("8B1G2CB500", 254, 266, 285, 291, 317, 331, 353, 358, 376, 446, 469, 558),
    ("8B1G2CB600", 271, 285, 306, 312, 340, 345, 369, 375, 393, 453, 476, 567),
    ("8B1G2CB700", 295, 318, 345, 338, 371, 375, 400, 414, 436, 565, 592, 720),
    ("8B1G2CB800", 315, 341, 371, 365, 402, 436, 470, 479, 506, 581, 608, 840),
    ("8B1G2CB900", 337, 365, 399, 401, 443, 475, 512, 523, 552, 604, 631, 758),
    ("8B1G2CB1000", 372, 390, 426, 449, 501, 547, 594, 607, 645, 738, 776, 942),
    ("8B1G2CB1200", 403, 425, 465, 485, 541, 606, 659, 672, 715, 758, 797, 963),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 400mm + 2 cajones 200mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 151, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 400mm + 2 cajones 200mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G2CL300", 372, 390, 426, 449, 501, 547, 594, 607, 645, 738, 776, 942),
    ("8B1G2CL350", 403, 425, 465, 485, 541, 606, 659, 672, 715, 758, 797, 963),
    ("8B1G2CL400", 318, 322, 334, 344, 362, 397, 416, 421, 436, 490, 510, 588),
    ("8B1G2CL450", 331, 339, 354, 357, 376, 414, 435, 440, 457, 513, 536, 620),
    ("8B1G2CL500", 341, 351, 366, 371, 392, 421, 442, 447, 464, 523, 545, 629),
    ("8B1G2CL600", 352, 362, 379, 385, 408, 431, 453, 458, 476, 545, 568, 656),
    ("8B1G2CL700", 362, 374, 393, 399, 425, 439, 461, 466, 484, 554, 578, 666),
    ("8B1G2CL800", 379, 393, 414, 420, 448, 454, 477, 483, 501, 561, 584, 675),
    ("8B1G2CL900", 403, 427, 454, 446, 479, 509, 544, 523, 544, 673, 701, 828),
    ("8B1G2CL1000", 423, 449, 480, 474, 510, 544, 579, 587, 614, 689, 717, 844),
    ("8B1G2CL1200", 445, 474, 509, 509, 552, 583, 622, 631, 662, 712, 739, 866),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 400mm + 2 cajones 200mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 151, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 152 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 2 caceroleros 400mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2GB300", 182, 184, 192, 195, 208, 234, 248, 251, 261, 293, 306, 358),
    ("8B2GB350", 196, 204, 217, 206, 219, 254, 271, 275, 288, 308, 322, 378),
    ("8B2GB400", 205, 214, 228, 218, 234, 263, 279, 284, 297, 320, 335, 391),
    ("8B2GB450", 214, 224, 239, 231, 248, 270, 287, 291, 305, 333, 348, 402),
    ("8B2GB500", 224, 234, 251, 243, 263, 279, 298, 302, 316, 345, 360, 415),
    ("8B2GB600", 233, 246, 263, 257, 278, 298, 317, 322, 337, 347, 362, 422),
    ("8B2GB700", 259, 289, 314, 291, 317, 315, 335, 355, 373, 408, 427, 499),
    ("8B2GB800", 276, 309, 337, 311, 340, 374, 403, 411, 433, 428, 446, 519),
    ("8B2GB900", 295, 330, 361, 345, 381, 385, 414, 421, 444, 460, 479, 549),
    ("8B2GB1000", 322, 334, 363, 369, 406, 442, 478, 487, 516, 531, 544, 633),
    ("8B2GB1200", 340, 353, 382, 386, 424, 461, 497, 505, 533, 550, 563, 652),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 400mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 152, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 400mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2GL300", 257, 259, 268, 271, 284, 310, 323, 327, 337, 369, 381, 434),
    ("8B2GL350", 271, 279, 292, 281, 295, 330, 345, 351, 363, 383, 398, 454),
    ("8B2GL400", 280, 289, 303, 294, 309, 338, 355, 359, 372, 396, 411, 466),
    ("8B2GL450", 290, 299, 315, 307, 323, 345, 362, 366, 380, 408, 423, 478),
    ("8B2GL500", 299, 310, 327, 318, 338, 355, 373, 377, 392, 421, 435, 490),
    ("8B2GL600", 309, 320, 338, 333, 354, 373, 393, 397, 413, 421, 437, 498),
    ("8B2GL700", 334, 363, 390, 365, 392, 390, 411, 431, 447, 483, 502, 574),
    ("8B2GL800", 351, 383, 412, 385, 415, 449, 478, 485, 507, 503, 522, 593),
    ("8B2GL900", 370, 404, 436, 421, 456, 460, 488, 497, 519, 534, 553, 624),
    ("8B2GL1000", 397, 408, 438, 442, 481, 517, 552, 562, 589, 606, 618, 708),
    ("8B2GL1200", 415, 426, 457, 461, 499, 534, 570, 580, 608, 624, 637, 726),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 400mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 152, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta extraible BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1PEB450", 167, 171, 181, 183, 195, 206, 218, 222, 230, 226, 231, 260),
    ("8B1PEB500", 173, 177, 188, 191, 205, 215, 229, 232, 242, 233, 238, 268),
    ("8B1PEB600", 186, 190, 203, 209, 226, 228, 242, 245, 255, 248, 254, 284),
    ("8B1PEB650", 216, 220, 235, 242, 262, 264, 280, 284, 296, 287, 295, 329),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta extraible BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 152, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 153 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta extraible LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1PEL450", 203, 207, 218, 221, 235, 248, 261, 266, 276, 270, 277, 311),
    ("8B1PEL500", 210, 215, 227, 230, 247, 259, 274, 277, 289, 279, 286, 319),
    ("8B1PEL600", 225, 230, 244, 251, 271, 273, 289, 293, 305, 296, 303, 337),
    ("8B1PEL650", 261, 267, 283, 291, 314, 317, 335, 340, 353, 343, 352, 391),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta extraible LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 153, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BRA930", 303, 312, 330, 327, 349, 399, 424, 431, 450, 454, 478, 544),
    ("8BRA1030", 343, 352, 374, 377, 405, 442, 470, 478, 500, 502, 517, 591),
    ("8BRA1080", 364, 374, 397, 403, 435, 470, 501, 508, 532, 526, 541, 615),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo rincón angular 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 153, "width": 93, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón angular 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BRA1P930", 295, 302, 318, 312, 331, 386, 410, 416, 434, 440, 456, 532),
    ("8BRA2P1030", 332, 339, 355, 349, 368, 423, 446, 453, 470, 477, 492, 569),
    ("8BRA2P1080", 369, 376, 392, 385, 404, 460, 483, 489, 507, 513, 529, 606),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo rincón angular 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 153, "width": 93, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BRL1P900", 179, 185, 193, 187, 200, 228, 243, 243, 253, 274, 282, 320),
    ("8BRL1P1030", 182, 187, 196, 190, 203, 231, 246, 246, 256, 277, 286, 322),
    ("8BRL1P1000", 188, 194, 205, 200, 213, 239, 255, 255, 267, 286, 299, 332),
    ("8BRL1P1050", 194, 201, 212, 209, 225, 244, 259, 260, 272, 294, 307, 339),
    ("8BRL1P1100", 201, 207, 218, 216, 234, 253, 270, 271, 284, 302, 310, 347),
    ("8BRL1P1150", 207, 213, 227, 226, 245, 264, 281, 282, 296, 311, 318, 355),
    ("8BRL1P1200", 217, 225, 239, 243, 265, 274, 293, 294, 309, 326, 333, 370),
    ("8BRL1P1250", 226, 233, 248, 251, 273, 282, 301, 302, 317, 334, 341, 378),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo rincón lineal 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 153, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 154 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo rincón lineal 2 puertas (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BRL2P1200", 254, 264, 280, 271, 293, 349, 375, 378, 399, 422, 438, 513),
    ("8BRL2P1400", 286, 296, 317, 314, 342, 380, 410, 413, 435, 462, 485, 552),
    ("8BRL2P1500", 301, 312, 334, 335, 366, 403, 434, 439, 462, 482, 498, 572),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo rincón lineal 2 puertas (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 154, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo terminal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BTER1P300", 143, 146, 155, 153, 165, 190, 203, 206, 216, 217, 230, 263),
    ("8BTER1P350", 149, 153, 163, 163, 175, 194, 208, 211, 221, 226, 237, 271),
    ("8BTER1P400", 155, 160, 170, 172, 186, 205, 218, 223, 233, 234, 242, 279),
    ("8BTER1P450", 162, 167, 179, 182, 197, 215, 230, 234, 246, 244, 250, 288),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo terminal 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 154, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF1P450", 134, 139, 149, 151, 165, 184, 197, 202, 212, 213, 221, 258),
    ("8BF1P500", 142, 146, 158, 161, 176, 194, 210, 213, 225, 223, 230, 267),
    ("8BF1P600", 155, 161, 173, 181, 200, 208, 225, 228, 240, 240, 248, 285),
    ("8BF1P650", 174, 180, 194, 202, 223, 233, 252, 255, 269, 269, 278, 319),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 154, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF2P600", 182, 189, 206, 198, 217, 273, 297, 302, 321, 328, 342, 419),
    ("8BF2P700", 196, 204, 222, 218, 240, 292, 317, 323, 343, 345, 371, 437),
    ("8BF2P800", 210, 218, 237, 238, 263, 301, 327, 333, 354, 363, 385, 454),
    ("8BF2P900", 227, 235, 256, 260, 289, 326, 353, 360, 382, 384, 399, 475),
    ("8BF2P1000", 243, 252, 275, 281, 313, 349, 379, 386, 411, 404, 419, 494),
    ("8BF2P1200", 272, 281, 309, 322, 359, 377, 410, 418, 443, 442, 456, 529),
    ("8BF2P1300", 307, 318, 349, 364, 406, 426, 463, 472, 501, 500, 515, 598),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 154, "width": extract_width(ref), "height": 80, "depth": 58,
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
    product["visualType"] = "bajo"
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
print(f"RESUMEN - PÁGINAS 150-154")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
