#!/usr/bin/env python3
"""
Process pages 160-164 from TARIFA-TECNICA-ZONACOCINAS
Page 160: BAJOS 80cm FONDO ESTÁNDAR (hornos)
Pages 161-164: BAJOS 80cm FONDO 33cm
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
# PAGE 160 - BAJOS 80cm FONDO ESTÁNDAR (hornos)
# ============================================

# Bajo 1 cajón 160mm BAX + horno 600mm + 1 regleta superior
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPH1CB600", 163, 161, 169, 159, 167, 174, 183, 184, 190, 204, 208, 205),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cajón 160mm BAX + horno 600mm + 1 regleta superior",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 160, "width": 60, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cajón 140mm LUX + horno 600mm + 1 regleta superior
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPH1CL600", 189, 187, 195, 185, 193, 201, 209, 210, 216, 229, 234, 231),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cajón 140mm LUX + horno 600mm + 1 regleta superior",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 160, "width": 60, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 350 BAX + horno 450mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPH451GB600", 161, 164, 171, 176, 186, 182, 189, 191, 196, 221, 229, 259),
    ("8BPH451GB900", 195, 200, 209, 215, 230, 242, 255, 258, 268, 289, 303, 343),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 350 BAX + horno 450mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 160, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 350 LUX + horno 450mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BPH451GL600", 190, 192, 200, 205, 215, 210, 217, 219, 225, 249, 257, 288),
    ("8BPH451GL900", 224, 228, 238, 244, 258, 270, 284, 287, 296, 317, 332, 372),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 350 LUX + horno 450mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 160, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 161 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 1 puerta fondo 330 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1PX300", 88, 91, 100, 97, 106, 133, 145, 148, 158, 161, 168, 206),
    ("8B1PX350", 93, 98, 107, 105, 116, 142, 154, 158, 169, 169, 181, 214),
    ("8B1PX400", 100, 104, 113, 114, 126, 146, 159, 162, 172, 176, 188, 222),
    ("8B1PX450", 106, 110, 121, 123, 137, 155, 169, 173, 184, 185, 192, 230),
    ("8B1PX500", 112, 117, 128, 131, 147, 165, 181, 184, 196, 193, 201, 237),
    ("8B1PX600", 125, 129, 143, 150, 168, 177, 193, 197, 210, 210, 216, 254),
    ("8B1PX650", 151, 155, 169, 176, 194, 204, 219, 224, 236, 236, 243, 280),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta fondo 330 (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 161, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2PX600", 151, 159, 174, 168, 187, 243, 266, 272, 290, 296, 312, 389),
    ("8B2PX700", 164, 171, 189, 186, 208, 259, 285, 291, 311, 313, 338, 404),
    ("8B2PX800", 175, 184, 204, 204, 229, 267, 293, 299, 319, 330, 352, 420),
    ("8B2PX900", 190, 198, 219, 224, 252, 288, 316, 323, 345, 348, 362, 438),
    ("8B2PX1000", 203, 212, 235, 242, 273, 309, 339, 347, 371, 364, 379, 454),
    ("8B2PX1200", 227, 236, 264, 277, 314, 333, 364, 373, 398, 397, 411, 485),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas fondo 330",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 161, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 vitrina fondo 330 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1VX300", 137, 127, 134, 132, 142, 155, 168, 170, 180, 183, 190, 229),
    ("8B1VX350", 145, 137, 145, 145, 155, 167, 180, 183, 193, 194, 207, 239),
    ("8B1VX400", 152, 146, 156, 156, 169, 175, 188, 191, 202, 206, 217, 251),
    ("8B1VX450", 161, 155, 167, 169, 184, 188, 202, 206, 216, 218, 226, 263),
    ("8B1VX500", 169, 166, 177, 182, 197, 202, 217, 221, 232, 230, 237, 274),
    ("8B1VX600", 185, 186, 200, 207, 226, 221, 237, 240, 254, 253, 260, 297),
    ("8B1VX650", 202, 203, 216, 224, 243, 237, 254, 257, 271, 270, 277, 314),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 vitrina fondo 330 (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 161, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 vitrinas fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2VX600", 248, 228, 244, 238, 257, 286, 310, 315, 334, 340, 355, 432),
    ("8B2VX700", 264, 248, 266, 264, 286, 310, 335, 341, 361, 363, 389, 455),
    ("8B2VX800", 280, 267, 287, 289, 313, 324, 351, 357, 377, 387, 410, 477),
    ("8B2VX900", 296, 287, 308, 313, 341, 351, 379, 386, 408, 411, 425, 500),
    ("8B2VX1000", 312, 307, 330, 338, 370, 378, 408, 416, 440, 434, 448, 523),
    ("8B2VX1200", 343, 345, 373, 387, 425, 416, 448, 456, 482, 481, 495, 568),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 vitrinas fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 161, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 162 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 1 puerta 640mm + 1 cajón 160mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1P1CBX300", 130, 131, 141, 134, 145, 165, 176, 180, 188, 206, 216, 246),
    ("8B1P1CBX350", 138, 139, 149, 143, 154, 170, 182, 185, 193, 214, 225, 254),
    ("8B1P1CBX400", 145, 146, 159, 151, 165, 175, 188, 191, 201, 224, 234, 263),
    ("8B1P1CBX450", 152, 154, 167, 161, 175, 187, 201, 204, 214, 232, 243, 271),
    ("8B1P1CBX500", 160, 163, 176, 170, 186, 195, 209, 213, 224, 240, 251, 279),
    ("8B1P1CBX600", 175, 179, 195, 188, 207, 213, 230, 233, 246, 258, 268, 296),
    ("8B1P1CBX650", 196, 200, 219, 211, 232, 239, 258, 261, 275, 289, 300, 332),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta 640mm + 1 cajón 160mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 162, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta 640mm + 1 cajón 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1P1CLX300", 163, 164, 173, 168, 177, 198, 210, 212, 222, 239, 250, 279),
    ("8B1P1CLX350", 170, 172, 183, 175, 187, 203, 214, 217, 227, 248, 258, 287),
    ("8B1P1CLX400", 177, 179, 191, 184, 197, 208, 221, 224, 233, 256, 267, 295),
    ("8B1P1CLX450", 185, 187, 200, 193, 208, 219, 232, 235, 246, 265, 274, 303),
    ("8B1P1CLX500", 192, 195, 209, 202, 217, 227, 242, 245, 256, 273, 282, 311),
    ("8B1P1CLX600", 207, 210, 227, 219, 238, 245, 261, 265, 277, 290, 299, 328),
    ("8B1P1CLX650", 232, 235, 254, 246, 267, 274, 293, 296, 310, 325, 335, 367),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta 640mm + 1 cajón 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 162, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 640mm + 1 cajón 160mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2P1CBX600", 202, 207, 225, 209, 229, 256, 276, 281, 296, 331, 350, 410),
    ("8B2P1CBX700", 217, 225, 246, 232, 255, 279, 301, 307, 324, 366, 397, 444),
    ("8B2P1CBX800", 234, 239, 263, 249, 275, 298, 322, 329, 348, 390, 414, 467),
    ("8B2P1CBX900", 251, 257, 284, 270, 299, 322, 349, 355, 376, 413, 433, 490),
    ("8B2P1CBX1000", 269, 274, 302, 288, 320, 339, 368, 375, 397, 431, 450, 507),
    ("8B2P1CBX1200", 299, 306, 338, 324, 362, 376, 407, 415, 440, 465, 485, 541),
    ("8B2P1CBX1300", 335, 342, 379, 363, 406, 421, 456, 465, 493, 521, 543, 606),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 162, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 640mm + 1 cajón 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2P1CLX600", 233, 237, 256, 240, 260, 288, 308, 312, 328, 362, 381, 441),
    ("8B2P1CLX700", 249, 255, 276, 263, 287, 310, 332, 337, 355, 397, 427, 475),
    ("8B2P1CLX800", 265, 270, 293, 279, 306, 329, 353, 358, 378, 420, 444, 498),
    ("8B2P1CLX900", 280, 288, 313, 299, 329, 352, 378, 385, 406, 442, 462, 520),
    ("8B2P1CLX1000", 298, 303, 332, 317, 349, 369, 397, 403, 425, 459, 480, 537),
    ("8B2P1CLX1200", 327, 334, 366, 353, 391, 403, 436, 443, 468, 492, 512, 568),
    ("8B2P1CLX1300", 366, 374, 410, 395, 437, 452, 488, 496, 524, 552, 574, 636),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 162, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 163 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 4 cajones 200mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B4CBX300", 224, 231, 245, 264, 286, 329, 354, 360, 379, 457, 484, 588),
    ("8B4CBX350", 234, 243, 258, 276, 301, 341, 368, 374, 394, 487, 518, 629),
    ("8B4CBX400", 246, 255, 273, 292, 318, 347, 373, 379, 399, 494, 523, 635),
    ("8B4CBX450", 260, 270, 288, 307, 333, 361, 387, 394, 414, 508, 538, 650),
    ("8B4CBX500", 268, 280, 302, 322, 355, 364, 392, 398, 420, 529, 562, 683),
    ("8B4CBX600", 291, 306, 331, 350, 385, 376, 403, 410, 431, 541, 572, 694),
    ("8B4CBX700", 313, 331, 359, 369, 406, 416, 447, 456, 480, 704, 740, 923),
    ("8B4CBX800", 335, 356, 387, 401, 445, 479, 519, 528, 560, 715, 752, 935),
    ("8B4CBX900", 359, 382, 417, 437, 486, 544, 592, 604, 642, 728, 764, 947),
    ("8B4CBX1000", 400, 425, 468, 510, 574, 631, 691, 706, 753, 923, 987, 1230),
    ("8B4CBX1200", 444, 476, 526, 563, 635, 729, 800, 818, 875, 945, 1009, 1252),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 4 cajones 200mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 163, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 4 cajones 200mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B4CLX300", 360, 366, 381, 399, 422, 465, 489, 496, 516, 593, 621, 723),
    ("8B4CLX350", 370, 377, 394, 412, 436, 476, 502, 508, 528, 623, 652, 764),
    ("8B4CLX400", 379, 389, 406, 425, 453, 480, 506, 512, 533, 627, 656, 769),
    ("8B4CLX450", 390, 400, 419, 440, 469, 491, 519, 525, 546, 656, 689, 810),
    ("8B4CLX500", 399, 412, 434, 454, 486, 496, 523, 529, 550, 660, 693, 814),
    ("8B4CLX600", 419, 435, 460, 478, 515, 505, 531, 539, 560, 670, 701, 823),
    ("8B4CLX700", 439, 457, 485, 495, 532, 543, 574, 582, 607, 830, 866, 1049),
    ("8B4CLX800", 459, 480, 511, 526, 569, 603, 643, 652, 684, 839, 876, 1058),
    ("8B4CLX900", 481, 503, 539, 559, 608, 684, 726, 737, 763, 849, 886, 1069),
    ("8B4CLX1000", 520, 545, 588, 629, 694, 751, 811, 825, 873, 1043, 1107, 1349),
    ("8B4CLX1200", 559, 590, 641, 677, 750, 843, 915, 932, 989, 1059, 1124, 1366),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 4 cajones 200mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 163, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 164 - BAJOS 80cm FONDO 33cm
# ============================================

# Bajo 5 cajones 160mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B5CBX300", 264, 253, 266, 260, 275, 316, 334, 338, 352, 371, 383, 377),
    ("8B5CBX350", 276, 267, 280, 271, 287, 321, 339, 343, 358, 381, 394, 387),
    ("8B5CBX400", 288, 279, 295, 282, 299, 329, 345, 350, 364, 393, 404, 398),
    ("8B5CBX450", 300, 292, 309, 293, 311, 348, 366, 372, 387, 404, 416, 410),
    ("8B5CBX500", 312, 305, 323, 303, 322, 354, 373, 378, 394, 415, 427, 420),
    ("8B5CBX600", 337, 331, 352, 326, 348, 366, 385, 390, 406, 438, 449, 442),
    ("8B5CBX700", 369, 368, 396, 376, 407, 441, 470, 478, 501, 548, 622, 554),
    ("8B5CBX800", 400, 393, 423, 399, 432, 490, 526, 534, 563, 601, 644, 608),
    ("8B5CBX900", 423, 420, 454, 422, 457, 530, 569, 579, 610, 644, 668, 654),
    ("8B5CBX1000", 460, 446, 484, 444, 482, 543, 582, 591, 623, 667, 690, 676),
    ("8B5CBX1200", 509, 496, 540, 487, 529, 568, 607, 616, 647, 711, 840, 719),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 5 cajones 160mm BAX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 164, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 5 cajones 160mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B5CLX300", 434, 423, 436, 431, 445, 486, 504, 508, 522, 541, 553, 546),
    ("8B5CLX350", 444, 436, 449, 440, 455, 490, 508, 512, 526, 550, 563, 555),
    ("8B5CLX400", 456, 446, 462, 449, 466, 496, 513, 518, 531, 560, 572, 565),
    ("8B5CLX450", 466, 458, 475, 459, 477, 513, 532, 538, 552, 569, 582, 574),
    ("8B5CLX500", 477, 469, 488, 468, 487, 518, 538, 542, 558, 580, 591, 584),
    ("8B5CLX600", 498, 491, 513, 487, 508, 527, 547, 551, 567, 600, 611, 603),
    ("8B5CLX700", 526, 526, 553, 534, 565, 600, 629, 635, 658, 707, 780, 713),
    ("8B5CLX800", 555, 548, 579, 554, 587, 646, 681, 690, 718, 756, 799, 763),
    ("8B5CLX900", 576, 572, 606, 574, 609, 683, 722, 731, 762, 796, 820, 806),
    ("8B5CLX1000", 610, 595, 633, 593, 631, 692, 732, 741, 772, 816, 839, 825),
    ("8B5CLX1200", 652, 639, 684, 631, 673, 711, 751, 759, 791, 855, 878, 863),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 5 cajones 160mm LUX fondo 330mm",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO 33cm",
        "sourcePage": 164, "width": extract_width(ref), "height": 80, "depth": 33,
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
print(f"RESUMEN - PÁGINAS 160-164")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
