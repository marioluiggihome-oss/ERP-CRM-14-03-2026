#!/usr/bin/env python3
"""
Process pages 165-169 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS 80cm FONDO 33cm (continuación)
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
# PAGE 165 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 320mm + 3 cajones 160mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G3CBX300", 236, 231, 243, 243, 256, 292, 310, 314, 327, 357, 371, 393),
    ("8B1G3CBX350", 247, 243, 255, 253, 269, 300, 318, 322, 420, 372, 386, 411),
    ("8B1G3CBX400", 257, 254, 268, 264, 281, 307, 323, 328, 341, 380, 395, 419),
    ("8B1G3CBX450", 268, 265, 280, 275, 293, 322, 341, 345, 361, 395, 410, 436),
    ("8B1G3CBX500", 278, 277, 294, 287, 307, 328, 347, 352, 366, 403, 419, 444),
    ("8B1G3CBX600", 300, 299, 319, 310, 332, 339, 358, 362, 378, 421, 436, 462),
    ("8B1G3CBX700", 327, 330, 354, 347, 376, 394, 419, 425, 446, 534, 593, 593),
    ("8B1G3CBX800", 353, 352, 380, 371, 403, 442, 474, 481, 506, 570, 610, 629),
    ("8B1G3CBX900", 375, 377, 407, 394, 429, 485, 522, 530, 560, 601, 629, 660),
    ("8B1G3CBX1000", 414, 412, 447, 422, 462, 528, 570, 580, 613, 639, 660, 697),
    ("8B1G3CBX1200", 450, 448, 488, 456, 498, 551, 592, 602, 635, 674, 695, 731),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 320mm + 3 cajones 160mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 165, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 320mm + 3 cajones 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G3CLX300", 375, 370, 381, 381, 396, 432, 448, 453, 466, 496, 509, 531),
    ("8B1G3CLX350", 384, 380, 393, 391, 406, 438, 456, 460, 474, 509, 524, 548),
    ("8B1G3CLX400", 394, 391, 404, 400, 418, 443, 460, 464, 478, 517, 531, 555),
    ("8B1G3CLX450", 403, 400, 416, 411, 428, 458, 477, 481, 496, 530, 545, 571),
    ("8B1G3CLX500", 413, 411, 428, 421, 441, 462, 481, 485, 501, 538, 552, 579),
    ("8B1G3CLX600", 433, 432, 452, 441, 464, 470, 489, 495, 509, 552, 567, 593),
    ("8B1G3CLX700", 456, 459, 483, 476, 505, 523, 548, 554, 575, 665, 722, 722),
    ("8B1G3CLX800", 480, 479, 507, 498, 530, 569, 601, 608, 633, 697, 737, 756),
    ("8B1G3CLX900", 499, 501, 531, 519, 553, 610, 647, 655, 684, 725, 754, 785),
    ("8B1G3CLX1000", 536, 533, 569, 545, 584, 651, 692, 702, 735, 762, 783, 819),
    ("8B1G3CLX1200", 568, 566, 606, 573, 615, 668, 710, 719, 753, 792, 812, 848),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 320mm + 3 cajones 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 165, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 166 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 2 caceroleros 320mm +1 cajon 160mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2G1CBX300", 208, 208, 218, 224, 238, 269, 286, 289, 302, 342, 359, 408),
    ("8B2G1CBX350", 216, 217, 230, 234, 250, 279, 296, 300, 314, 361, 378, 433),
    ("8B2G1CBX400", 227, 228, 242, 246, 263, 285, 301, 306, 319, 368, 384, 439),
    ("8B2G1CBX450", 236, 238, 252, 257, 276, 297, 315, 320, 334, 385, 404, 463),
    ("8B2G1CBX500", 246, 249, 265, 269, 290, 302, 320, 324, 339, 392, 411, 469),
    ("8B2G1CBX600", 265, 269, 287, 293, 317, 312, 331, 335, 350, 403, 422, 481),
    ("8B2G1CBX700", 285, 291, 313, 316, 344, 345, 368, 374, 394, 521, 565, 631),
    ("8B2G1CBX800", 306, 312, 420, 342, 374, 394, 421, 428, 450, 539, 576, 649),
    ("8B2G1CBX900", 326, 334, 360, 366, 401, 440, 474, 482, 508, 557, 590, 668),
    ("8B2G1CBX1000", 368, 376, 411, 401, 442, 515, 558, 568, 603, 613, 631, 718),
    ("8B2G1CBX1200", 392, 401, 437, 424, 466, 533, 578, 588, 623, 637, 655, 741),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 320mm +1 cajon 160mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 166, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 320mm +1 cajon 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2G1CLX300", 315, 316, 327, 332, 347, 377, 393, 397, 410, 450, 466, 517),
    ("8B2G1CLX350", 323, 324, 420, 341, 357, 386, 403, 407, 421, 468, 485, 540),
    ("8B2G1CLX400", 333, 334, 348, 352, 369, 391, 407, 412, 425, 474, 490, 545),
    ("8B2G1CLX450", 341, 343, 357, 362, 381, 402, 420, 425, 440, 491, 509, 568),
    ("8B2G1CLX500", 350, 353, 369, 373, 394, 406, 424, 429, 443, 496, 515, 573),
    ("8B2G1CLX600", 366, 372, 390, 395, 419, 415, 433, 437, 452, 506, 524, 584),
    ("8B2G1CLX700", 385, 392, 413, 417, 444, 446, 468, 474, 491, 622, 666, 732),
    ("8B2G1CLX800", 404, 411, 435, 441, 473, 491, 519, 527, 549, 637, 675, 748),
    ("8B2G1CLX900", 422, 431, 457, 463, 498, 537, 571, 579, 606, 653, 688, 764),
    ("8B2G1CLX1000", 462, 471, 506, 496, 537, 609, 653, 664, 698, 709, 727, 813),
    ("8B2G1CLX1200", 483, 492, 528, 516, 558, 626, 670, 680, 714, 729, 747, 833),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 320mm +1 cajon 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 166, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 167 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 400mm + 2 cajones 200mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G2CBX300", 195, 200, 211, 223, 239, 274, 293, 298, 313, 368, 387, 465),
    ("8B1G2CBX350", 208, 215, 230, 234, 253, 291, 312, 317, 334, 391, 413, 497),
    ("8B1G2CBX400", 217, 227, 243, 247, 269, 297, 318, 323, 340, 399, 421, 505),
    ("8B1G2CBX450", 228, 237, 255, 261, 285, 307, 329, 334, 352, 421, 444, 532),
    ("8B1G2CBX500", 237, 249, 269, 275, 300, 314, 420, 342, 360, 429, 453, 541),
    ("8B1G2CBX600", 253, 267, 288, 295, 323, 329, 352, 357, 376, 435, 459, 550),
    ("8B1G2CBX700", 277, 300, 328, 320, 353, 356, 383, 396, 418, 547, 574, 702),
    ("8B1G2CBX800", 296, 322, 353, 347, 383, 417, 452, 460, 487, 562, 590, 717),
    ("8B1G2CBX900", 317, 347, 379, 381, 424, 455, 494, 503, 533, 584, 611, 738),
    ("8B1G2CBX1000", 351, 370, 406, 428, 480, 526, 574, 586, 624, 717, 756, 922),
    ("8B1G2CBX1200", 381, 403, 443, 463, 519, 584, 637, 650, 693, 736, 775, 941),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 400mm + 2 cajones 200mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 167, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 400mm + 2 cajones 200mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G2CLX300", 300, 305, 316, 327, 344, 379, 398, 403, 418, 473, 492, 570),
    ("8B1G2CLX350", 312, 319, 334, 337, 357, 394, 415, 421, 437, 494, 517, 601),
    ("8B1G2CLX400", 320, 330, 345, 350, 372, 400, 421, 426, 443, 502, 524, 608),
    ("8B1G2CLX450", 330, 339, 357, 363, 386, 408, 431, 436, 454, 523, 546, 634),
    ("8B1G2CLX500", 339, 351, 370, 376, 402, 415, 438, 443, 461, 530, 553, 642),
    ("8B1G2CLX600", 353, 366, 387, 394, 423, 427, 450, 457, 475, 534, 559, 649),
    ("8B1G2CLX700", 375, 398, 425, 418, 450, 454, 480, 494, 516, 645, 672, 799),
    ("8B1G2CLX800", 392, 418, 448, 443, 479, 513, 547, 555, 583, 657, 686, 813),
    ("8B1G2CLX900", 412, 440, 473, 476, 518, 549, 587, 596, 627, 678, 706, 833),
    ("8B1G2CLX1000", 443, 462, 498, 521, 572, 618, 667, 678, 716, 810, 847, 1013),
    ("8B1G2CLX1200", 470, 491, 531, 552, 608, 672, 725, 739, 781, 825, 863, 1029),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 400mm + 2 cajones 200mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 167, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 168 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 2 caceroleros 400mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2GBX300", 166, 168, 177, 180, 192, 218, 232, 235, 246, 277, 291, 342),
    ("8B2GBX350", 180, 188, 201, 190, 204, 238, 254, 259, 272, 292, 307, 362),
    ("8B2GBX400", 189, 197, 211, 202, 217, 247, 263, 267, 280, 303, 318, 374),
    ("8B2GBX450", 197, 207, 223, 214, 231, 253, 270, 274, 288, 316, 330, 385),
    ("8B2GBX500", 206, 216, 234, 226, 245, 263, 280, 285, 299, 329, 342, 397),
    ("8B2GBX600", 215, 227, 245, 239, 260, 279, 299, 303, 318, 328, 343, 404),
    ("8B2GBX700", 240, 270, 295, 271, 298, 296, 316, 336, 354, 390, 407, 480),
    ("8B2GBX800", 256, 289, 317, 291, 320, 354, 383, 391, 413, 408, 427, 499),
    ("8B2GBX900", 274, 310, 340, 326, 360, 365, 394, 401, 423, 440, 458, 528),
    ("8B2GBX1000", 301, 313, 342, 347, 385, 421, 457, 465, 494, 510, 523, 612),
    ("8B2GBX1200", 317, 330, 359, 363, 402, 438, 474, 482, 510, 527, 540, 629),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 400mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 168, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 400mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2GLX300", 240, 243, 252, 255, 267, 293, 307, 310, 320, 352, 365, 417),
    ("8B2GLX350", 254, 261, 275, 264, 277, 312, 329, 333, 347, 365, 380, 436),
    ("8B2GLX400", 261, 271, 285, 275, 291, 319, 336, 340, 354, 377, 392, 447),
    ("8B2GLX450", 270, 279, 295, 287, 303, 326, 343, 348, 360, 389, 403, 458),
    ("8B2GLX500", 278, 289, 306, 298, 317, 335, 353, 357, 371, 400, 415, 469),
    ("8B2GLX600", 286, 298, 315, 311, 331, 351, 370, 375, 390, 399, 415, 476),
    ("8B2GLX700", 310, 339, 365, 341, 368, 365, 386, 405, 423, 459, 478, 549),
    ("8B2GLX800", 324, 357, 385, 360, 390, 423, 452, 459, 482, 477, 496, 567),
    ("8B2GLX900", 342, 377, 407, 393, 427, 433, 461, 468, 490, 507, 525, 596),
    ("8B2GLX1000", 368, 379, 408, 413, 452, 487, 523, 531, 560, 576, 589, 678),
    ("8B2GLX1200", 381, 393, 423, 427, 465, 501, 537, 546, 574, 590, 603, 692),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 caceroleros 400mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 168, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Puerta de integracion electrodoméstico
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8CLV450", 40, 44, 55, 57, 70, 88, 103, 106, 118, 119, 126, 163),
    ("8CLV600", 50, 55, 68, 76, 93, 103, 119, 123, 135, 135, 142, 179),
]:
    products_to_add.append({
        "reference": ref, "name": "Puerta de integracion electrodoméstico",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 168, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 169 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 300 BAX + micro 400mm fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPM1GB600", 148, 151, 159, 164, 173, 169, 176, 179, 184, 208, 216, 247),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 300 BAX + micro 400mm fondo 330",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 169, "width": 60, "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 300 LUX + micro 400mm fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPM1LB600", 176, 179, 186, 191, 202, 196, 204, 206, 211, 235, 244, 274),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 300 LUX + micro 400mm fondo 330",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 169, "width": 60, "height": 80, "depth": 33,
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
print(f"RESUMEN - PÁGINAS 165-169")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
