#!/usr/bin/env python3
"""
Process pages 140-144 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS - BAJOS 70cm FONDO 33cm + DECORATIVOS
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
# PAGE 140 - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2G1CBX300", 203, 204, 214, 222, 236, 266, 281, 286, 298, 341, 357, 407),
    ("7B2G1CBX350", 211, 213, 225, 231, 247, 274, 291, 294, 308, 359, 376, 432),
    ("7B2G1CBX400", 221, 223, 235, 242, 258, 278, 295, 299, 312, 365, 382, 437),
    ("7B2G1CBX450", 229, 233, 246, 253, 271, 290, 307, 312, 326, 383, 402, 461),
    ("7B2G1CBX500", 238, 243, 257, 264, 284, 295, 312, 316, 330, 390, 407, 467),
    ("7B2G1CBX600", 255, 263, 279, 282, 306, 305, 321, 326, 339, 401, 419, 479),
    ("7B2G1CBX700", 275, 284, 303, 305, 330, 341, 362, 368, 385, 506, 540, 617),
    ("7B2G1CBX800", 294, 302, 324, 328, 356, 384, 412, 418, 439, 524, 551, 635),
    ("7B2G1CBX900", 313, 323, 348, 352, 383, 426, 459, 466, 491, 541, 564, 653),
    ("7B2G1CBX1000", 342, 352, 381, 394, 434, 475, 512, 522, 551, 646, 683, 800),
    ("7B2G1CBX1200", 378, 391, 424, 433, 477, 531, 575, 586, 619, 669, 706, 823),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 140, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 280mm + 1 cajón 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2G1CLX300", 309, 310, 319, 328, 341, 372, 387, 392, 404, 446, 463, 512),
    ("7B2G1CLX350", 316, 318, 330, 420, 352, 379, 395, 399, 413, 464, 481, 536),
    ("7B2G1CLX400", 324, 327, 339, 345, 362, 382, 399, 403, 416, 468, 486, 541),
    ("7B2G1CLX450", 332, 420, 349, 356, 374, 393, 411, 415, 428, 486, 505, 564),
    ("7B2G1CLX500", 340, 345, 359, 365, 385, 397, 414, 418, 432, 491, 510, 569),
    ("7B2G1CLX600", 356, 362, 379, 383, 405, 404, 422, 426, 440, 501, 520, 579),
    ("7B2G1CLX700", 373, 382, 402, 402, 427, 440, 461, 466, 484, 605, 637, 716),
    ("7B2G1CLX800", 391, 399, 421, 424, 453, 481, 508, 515, 536, 621, 648, 732),
    ("7B2G1CLX900", 407, 418, 443, 446, 478, 522, 553, 561, 586, 636, 659, 748),
    ("7B2G1CLX1000", 436, 445, 475, 487, 527, 567, 605, 614, 645, 738, 775, 894),
    ("7B2G1CLX1200", 467, 480, 513, 522, 566, 620, 663, 674, 707, 758, 795, 912),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 280mm + 1 cajón 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 140, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 141 - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G2CBX300", 190, 188, 196, 197, 209, 236, 250, 253, 265, 290, 301, 324),
    ("7B1G2CBX350", 200, 197, 207, 207, 219, 244, 258, 261, 272, 303, 315, 340),
    ("7B1G2CBX400", 208, 206, 217, 216, 230, 249, 263, 266, 277, 310, 322, 348),
    ("7B1G2CBX450", 217, 215, 228, 226, 240, 261, 277, 280, 292, 323, 420, 363),
    ("7B1G2CBX500", 226, 225, 238, 235, 251, 267, 281, 286, 297, 330, 342, 370),
    ("7B1G2CBX600", 244, 244, 259, 254, 273, 276, 291, 295, 307, 343, 356, 383),
    ("7B1G2CBX700", 264, 267, 286, 282, 306, 316, 420, 341, 357, 437, 480, 494),
    ("7B1G2CBX800", 285, 286, 307, 302, 329, 356, 380, 386, 406, 462, 494, 519),
    ("7B1G2CBX900", 302, 306, 330, 322, 351, 393, 421, 427, 450, 484, 508, 543),
    ("7B1G2CBX1000", 420, 420, 364, 348, 379, 434, 467, 476, 502, 521, 537, 575),
    ("7B1G2CBX1200", 364, 365, 396, 374, 407, 453, 486, 495, 521, 547, 564, 603),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 141, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G2CLX300", 293, 290, 299, 300, 312, 339, 353, 356, 368, 393, 404, 427),
    ("7B1G2CLX350", 301, 298, 309, 309, 321, 345, 360, 363, 375, 404, 417, 442),
    ("7B1G2CLX400", 309, 307, 318, 317, 331, 350, 363, 368, 378, 411, 423, 448),
    ("7B1G2CLX450", 317, 315, 328, 326, 340, 361, 377, 380, 392, 423, 436, 463),
    ("7B1G2CLX500", 324, 324, 338, 334, 351, 365, 380, 384, 396, 428, 442, 469),
    ("7B1G2CLX600", 340, 341, 357, 352, 370, 373, 389, 392, 404, 441, 454, 481),
    ("7B1G2CLX700", 359, 362, 381, 378, 401, 412, 432, 437, 453, 531, 575, 589),
    ("7B1G2CLX800", 378, 379, 401, 396, 422, 449, 475, 480, 500, 555, 587, 612),
    ("7B1G2CLX900", 395, 398, 421, 415, 442, 484, 512, 520, 542, 576, 601, 635),
    ("7B1G2CLX1000", 425, 426, 455, 438, 469, 524, 558, 566, 592, 611, 627, 666),
    ("7B1G2CLX1200", 450, 452, 482, 460, 494, 540, 573, 581, 608, 634, 650, 689),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 141, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 142 - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 2 caceroleros 350mm BAX fondo 330mm (Note: 7B2GBX not 7B1G2CBX)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2GBX300", 162, 164, 172, 179, 190, 212, 225, 228, 238, 275, 289, 340),
    ("7B2GBX350", 169, 171, 181, 187, 200, 222, 235, 238, 250, 292, 307, 362),
    ("7B2GBX400", 176, 180, 189, 196, 210, 226, 239, 243, 253, 296, 311, 366),
    ("7B2GBX450", 184, 188, 198, 206, 222, 235, 250, 253, 265, 313, 329, 390),
    ("7B2GBX500", 191, 196, 208, 216, 234, 239, 254, 257, 269, 317, 333, 394),
    ("7B2GBX600", 206, 212, 226, 236, 257, 248, 263, 266, 277, 326, 341, 402),
    ("7B2GBX700", 222, 228, 244, 251, 273, 268, 284, 288, 301, 421, 450, 530),
    ("7B2GBX800", 236, 245, 261, 273, 298, 307, 328, 332, 349, 429, 459, 539),
    ("7B2GBX900", 253, 261, 281, 294, 321, 347, 372, 378, 399, 440, 469, 549),
    ("7B2GBX1000", 288, 300, 327, 324, 358, 419, 455, 463, 491, 494, 506, 595),
    ("7B2GBX1200", 305, 316, 343, 341, 375, 435, 470, 479, 508, 509, 523, 612),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 142, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 350mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2GLX300", 234, 236, 245, 251, 263, 285, 297, 300, 311, 348, 361, 413),
    ("7B2GLX350", 240, 244, 252, 258, 272, 294, 308, 311, 321, 363, 378, 435),
    ("7B2GLX400", 248, 251, 260, 268, 281, 297, 311, 314, 324, 368, 382, 438),
    ("7B2GLX450", 254, 258, 269, 277, 293, 307, 320, 324, 420, 383, 400, 460),
    ("7B2GLX500", 261, 266, 278, 287, 305, 310, 324, 328, 339, 387, 403, 464),
    ("7B2GLX600", 275, 280, 295, 306, 326, 317, 331, 335, 347, 394, 411, 470),
    ("7B2GLX700", 289, 295, 311, 318, 340, 335, 352, 356, 369, 489, 519, 599),
    ("7B2GLX800", 302, 311, 329, 340, 365, 373, 394, 399, 416, 497, 526, 605),
    ("7B2GLX900", 318, 327, 347, 359, 386, 412, 437, 443, 464, 505, 534, 614),
    ("7B2GLX1000", 352, 364, 391, 389, 422, 483, 519, 527, 555, 557, 570, 659),
    ("7B2GLX1200", 365, 378, 404, 402, 436, 497, 532, 541, 569, 571, 584, 674),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 142, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Puerta de integración electrodoméstico
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7CLV450", 35, 39, 48, 44, 56, 60, 69, 71, 79, 93, 101, 131),
    ("7CLV600", 44, 48, 60, 59, 74, 77, 88, 91, 101, 106, 114, 144),
]:
    products_to_add.append({
        "reference": ref, "name": "Puerta de integración electrodoméstico",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 142, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 143 - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 300 BAX + micro 400mm fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BPM1GB600", 124, 128, 134, 139, 148, 145, 152, 153, 159, 187, 194, 225),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 300 BAX + micro 400mm fondo 330",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 143, "width": 60, "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 300 LUX + micro 400mm fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BPM1LB600", 137, 141, 147, 151, 161, 158, 165, 166, 171, 200, 207, 237),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 300 LUX + micro 400mm fondo 330",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 143, "width": 60, "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo botellero cuadros (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BBOT150", 260, 298, 255, 231, 266, 322, 359, 322, 347, 335, 340, 335),
    ("7BBOT300", 389, 446, 370, 328, 388, 464, 522, 464, 502, 484, 491, 484),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo botellero cuadros (3 estantes)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 143, "width": extract_width(ref), "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo terminal abierto (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BTER300", 129, 163, 203, 163, 203, 177, 204, 177, 195, 157, 159, 157),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo terminal abierto (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 143, "width": 30, "height": 70, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 144 - BAJOS 70cm DECORATIVOS
# ============================================

# Bajo decorativo fondo 580mm (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BDEC150", 195, 229, 189, 168, 198, 244, 275, 244, 265, 255, 258, 255),
    ("7BDEC200", 221, 257, 212, 189, 223, 279, 314, 279, 302, 291, 296, 291),
    ("7BDEC300", 222, 260, 216, 191, 227, 287, 324, 287, 311, 299, 303, 299),
    ("7BDEC350", 258, 298, 251, 223, 264, 334, 377, 334, 362, 349, 354, 349),
    ("7BDEC400", 265, 309, 256, 226, 269, 350, 397, 350, 381, 366, 372, 366),
    ("7BDEC450", 278, 322, 270, 239, 284, 364, 412, 364, 395, 380, 385, 380),
    ("7BDEC500", 296, 343, 293, 260, 309, 384, 435, 384, 418, 402, 407, 402),
    ("7BDEC600", 345, 396, 327, 290, 343, 413, 466, 413, 448, 431, 438, 431),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo decorativo fondo 580mm (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm DECORATIVOS",
        "sourcePage": 144, "width": extract_width(ref), "height": 70, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo decorativo fondo 330mm (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BDECX150", 152, 175, 148, 134, 154, 184, 197, 184, 197, 191, 191, 191),
    ("7BDECX200", 166, 188, 161, 146, 169, 194, 208, 194, 208, 201, 201, 201),
    ("7BDECX300", 172, 195, 165, 148, 173, 205, 212, 205, 221, 212, 212, 212),
    ("7BDECX350", 197, 227, 194, 174, 203, 239, 250, 239, 257, 250, 250, 250),
    ("7BDECX400", 201, 234, 197, 175, 207, 254, 275, 254, 275, 265, 265, 265),
    ("7BDECX450", 205, 238, 201, 180, 210, 257, 278, 257, 278, 268, 268, 268),
    ("7BDECX500", 221, 253, 215, 193, 226, 275, 297, 275, 297, 287, 287, 287),
    ("7BDECX600", 237, 269, 230, 206, 240, 296, 319, 296, 319, 309, 309, 309),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo decorativo fondo 330mm (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 70cm DECORATIVOS",
        "sourcePage": 144, "width": extract_width(ref), "height": 70, "depth": 33,
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
print(f"RESUMEN - PÁGINAS 140-144")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
