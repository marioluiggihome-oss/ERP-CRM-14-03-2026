#!/usr/bin/env python3
"""
Process pages 155-159 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS 80cm FONDO ESTÁNDAR (Fregaderos y Bajos Placa)
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
# PAGE 155 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo Fregadero 2 caceroleros 400mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF2GB600", 257, 270, 287, 281, 302, 322, 341, 347, 361, 371, 386, 446),
    ("8BF2GB700", 285, 314, 339, 316, 342, 340, 360, 380, 398, 434, 453, 524),
    ("8BF2GB800", 302, 334, 362, 337, 366, 400, 428, 436, 459, 455, 473, 544),
    ("8BF2GB900", 323, 358, 389, 374, 408, 414, 442, 449, 471, 488, 506, 578),
    ("8BF2GB1000", 353, 364, 394, 398, 437, 473, 508, 517, 545, 562, 574, 664),
    ("8BF2GB1200", 374, 386, 416, 420, 458, 494, 530, 539, 567, 583, 596, 686),
    ("8BF2GB1300", 419, 433, 466, 470, 513, 553, 594, 603, 635, 653, 668, 768),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 2 caceroleros 400mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 155, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 2 caceroleros 400mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF2GL600", 334, 345, 363, 358, 378, 398, 418, 422, 438, 446, 462, 523),
    ("8BF2GL700", 360, 390, 416, 392, 418, 416, 437, 457, 474, 509, 528, 600),
    ("8BF2GL800", 378, 411, 439, 413, 442, 477, 505, 512, 534, 530, 548, 621),
    ("8BF2GL900", 399, 434, 464, 449, 485, 489, 518, 525, 548, 564, 582, 653),
    ("8BF2GL1000", 428, 440, 469, 474, 512, 548, 584, 592, 621, 637, 650, 739),
    ("8BF2GL1200", 449, 461, 490, 495, 533, 569, 605, 614, 642, 658, 671, 760),
    ("8BF2GL1300", 503, 516, 549, 554, 597, 637, 677, 688, 719, 737, 751, 851),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 2 caceroleros 400mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 155, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 1 puerta extraible BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF1PEB450", 165, 169, 180, 182, 195, 214, 228, 232, 243, 244, 251, 289),
    ("8BF1PEB500", 172, 177, 189, 192, 208, 226, 240, 245, 256, 254, 260, 298),
    ("8BF1PEB600", 188, 193, 207, 213, 232, 242, 257, 261, 274, 273, 280, 317),
    ("8BF1PEB700", 212, 217, 231, 237, 256, 266, 281, 286, 298, 297, 305, 341),
    ("8BF1PEB800", 236, 242, 255, 261, 280, 290, 306, 310, 322, 321, 329, 365),
    ("8BF1PEB900", 260, 266, 279, 286, 305, 314, 330, 334, 347, 345, 353, 390),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 1 puerta extraible BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 155, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 156 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo Fregadero 1 puerta extraible LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BF1PEL450", 202, 206, 217, 218, 233, 251, 265, 269, 281, 281, 289, 326),
    ("8BF1PEL500", 210, 214, 226, 229, 245, 263, 278, 281, 294, 291, 298, 335),
    ("8BF1PEL600", 226, 230, 244, 250, 269, 278, 294, 298, 311, 311, 317, 354),
    ("8BF1PEL700", 255, 259, 273, 279, 298, 308, 323, 328, 340, 340, 347, 383),
    ("8BF1PEL800", 285, 289, 302, 309, 328, 337, 353, 357, 370, 370, 376, 413),
    ("8BF1PEL900", 314, 318, 332, 338, 357, 366, 382, 386, 399, 399, 405, 442),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero 1 puerta extraible LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 156, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BFRA930", 163, 169, 179, 171, 184, 212, 227, 227, 238, 258, 267, 305),
    ("8BFRA1030", 168, 174, 184, 176, 189, 217, 232, 232, 244, 264, 272, 310),
    ("8BFRA1080", 171, 179, 188, 183, 197, 224, 238, 239, 251, 270, 282, 315),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero rincón angular 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 156, "width": 93, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BFRL1P900", 163, 169, 179, 171, 184, 212, 227, 227, 238, 258, 267, 305),
    ("8BFRL1P950", 168, 174, 184, 176, 189, 217, 232, 232, 244, 264, 272, 310),
    ("8BFRL1P1000", 171, 179, 188, 183, 197, 224, 238, 239, 251, 270, 282, 315),
    ("8BFRL1P1050", 184, 190, 201, 197, 213, 233, 249, 249, 261, 284, 295, 329),
    ("8BFRL1P1100", 187, 193, 206, 204, 222, 240, 257, 257, 271, 289, 297, 334),
    ("8BFRL1P1150", 191, 197, 211, 210, 229, 248, 266, 267, 280, 295, 302, 339),
    ("8BFRL1P1200", 197, 205, 219, 223, 245, 254, 273, 274, 289, 306, 314, 350),
    ("8BFRL1P1250", 206, 213, 227, 231, 253, 263, 281, 282, 297, 314, 321, 358),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero rincón lineal 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 156, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón lineal 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BFRL2P1200", 234, 244, 261, 251, 273, 330, 356, 358, 379, 402, 418, 494),
    ("8BFRL2P1400", 258, 269, 290, 287, 315, 354, 382, 385, 407, 436, 458, 525),
    ("8BFRL2P1500", 271, 281, 303, 305, 420, 373, 403, 407, 432, 452, 466, 541),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Fregadero rincón lineal 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 156, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 157 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1P600", 180, 184, 197, 205, 224, 232, 249, 252, 265, 265, 272, 309),
    ("8BP1P650", 201, 206, 221, 229, 250, 260, 279, 282, 296, 296, 305, 346),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 157, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP2P600", 206, 213, 230, 223, 242, 297, 321, 327, 345, 352, 366, 443),
    ("8BP2P700", 224, 232, 250, 247, 268, 319, 344, 351, 371, 374, 398, 464),
    ("8BP2P800", 239, 248, 268, 268, 293, 331, 357, 363, 383, 394, 416, 483),
    ("8BP2P900", 266, 274, 295, 299, 328, 363, 392, 399, 421, 423, 438, 513),
    ("8BP2P1000", 274, 284, 308, 314, 344, 381, 411, 419, 442, 437, 450, 525),
    ("8BP2P1200", 308, 317, 344, 357, 395, 413, 445, 453, 479, 478, 491, 565),
    ("8BP2P1300", 340, 350, 377, 390, 427, 445, 478, 485, 511, 510, 524, 597),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 157, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 320mm + 3 cajones 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1G3CB600", 355, 355, 375, 364, 386, 394, 413, 417, 433, 476, 490, 517),
    ("8BP1G3CB700", 386, 390, 415, 406, 436, 454, 480, 486, 506, 595, 654, 653),
    ("8BP1G3CB800", 416, 416, 443, 434, 466, 506, 538, 545, 570, 633, 674, 692),
    ("8BP1G3CB900", 450, 453, 482, 469, 505, 561, 597, 606, 635, 676, 705, 736),
    ("8BP1G3CB1000", 486, 483, 520, 495, 533, 601, 643, 652, 685, 712, 733, 770),
    ("8BP1G3CB1200", 530, 529, 569, 537, 579, 631, 673, 683, 715, 755, 775, 811),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 cacerolero 320mm + 3 cajones 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 157, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 320mm + 3 cajones 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1G3CL600", 499, 499, 519, 508, 531, 538, 557, 562, 577, 620, 634, 660),
    ("8BP1G3CL700", 530, 533, 559, 550, 580, 597, 624, 630, 650, 739, 798, 798),
    ("8BP1G3CL800", 561, 560, 588, 579, 611, 650, 681, 689, 714, 778, 818, 837),
    ("8BP1G3CL900", 594, 596, 627, 613, 649, 705, 741, 750, 779, 820, 848, 880),
    ("8BP1G3CL1000", 630, 628, 664, 638, 678, 746, 787, 797, 830, 857, 877, 914),
    ("8BP1G3CL1200", 675, 673, 713, 680, 722, 776, 817, 827, 860, 899, 920, 956),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 cacerolero 320mm + 3 cajones 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 157, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 158 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 2 caceroleros 320mm 1 cajón 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP2G1CB600", 319, 323, 342, 348, 372, 366, 385, 390, 404, 459, 477, 536),
    ("8BP2G1CB700", 345, 352, 373, 377, 404, 406, 428, 434, 452, 582, 626, 692),
    ("8BP2G1CB800", 369, 376, 399, 406, 438, 457, 485, 492, 515, 603, 641, 713),
    ("8BP2G1CB900", 401, 410, 436, 441, 477, 516, 549, 558, 584, 632, 666, 743),
    ("8BP2G1CB1000", 439, 448, 483, 473, 513, 587, 630, 641, 675, 686, 704, 791),
    ("8BP2G1CB1200", 471, 481, 517, 504, 546, 614, 658, 669, 704, 717, 840, 822),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 2 caceroleros 320mm 1 cajón 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 158, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 caceroleros 320mm 1 cajón 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP2G1CL600", 416, 431, 452, 458, 486, 491, 515, 520, 539, 597, 622, 713),
    ("8BP2G1CL700", 445, 469, 497, 489, 521, 525, 551, 565, 586, 716, 743, 870),
    ("8BP2G1CL800", 468, 495, 525, 519, 555, 589, 624, 632, 659, 734, 762, 889),
    ("8BP2G1CL900", 501, 530, 563, 566, 608, 639, 677, 687, 717, 768, 796, 922),
    ("8BP2G1CL1000", 531, 550, 587, 609, 660, 707, 755, 767, 804, 898, 937, 1103),
    ("8BP2G1CL1200", 570, 592, 632, 652, 708, 773, 826, 839, 882, 925, 964, 1130),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 2 caceroleros 320mm 1 cajón 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 158, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 400mm + 2 cajones 200mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1G2CB600", 307, 321, 342, 349, 377, 382, 405, 411, 429, 488, 512, 604),
    ("8BP1G2CB700", 336, 360, 386, 380, 412, 414, 442, 456, 477, 606, 634, 761),
    ("8BP1G2CB800", 359, 385, 416, 410, 446, 480, 515, 523, 550, 625, 652, 779),
    ("8BP1G2CB900", 392, 421, 454, 456, 499, 529, 568, 578, 608, 658, 686, 813),
    ("8BP1G2CB1000", 422, 441, 477, 500, 551, 597, 646, 657, 695, 789, 826, 992),
    ("8BP1G2CB1200", 461, 483, 523, 543, 599, 663, 717, 730, 772, 816, 855, 1021),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 cacerolero 400mm + 2 cajones 200mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 158, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 400mm + 2 cajones 200mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1G2CL600", 426, 441, 462, 468, 497, 502, 525, 530, 549, 608, 632, 723),
    ("8BP1G2CL700", 456, 507, 507, 500, 531, 536, 562, 575, 596, 727, 754, 881),
    ("8BP1G2CL800", 479, 536, 536, 529, 566, 600, 634, 643, 670, 744, 773, 900),
    ("8BP1G2CL900", 511, 573, 573, 576, 618, 650, 688, 697, 728, 778, 806, 743),
    ("8BP1G2CL1000", 542, 643, 597, 620, 671, 717, 765, 777, 815, 908, 947, 1113),
    ("8BP1G2CL1200", 581, 587, 643, 663, 718, 783, 837, 849, 893, 936, 974, 1140),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 cacerolero 400mm + 2 cajones 200mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 158, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 159 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 2 caceroleros 400mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP2GB600", 270, 281, 299, 294, 315, 335, 354, 359, 374, 382, 399, 459),
    ("8BP2GB700", 300, 330, 356, 332, 358, 356, 377, 397, 414, 449, 468, 541),
    ("8BP2GB800", 320, 353, 381, 355, 384, 418, 447, 455, 477, 473, 490, 563),
    ("8BP2GB900", 350, 385, 416, 401, 436, 441, 469, 477, 499, 516, 533, 604),
    ("8BP2GB1000", 373, 385, 415, 419, 457, 492, 529, 538, 566, 582, 595, 684),
    ("8BP2GB1200", 398, 410, 440, 444, 482, 518, 553, 563, 591, 607, 621, 709),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 2 caceroleros 400mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 159, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 caceroleros 400mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP2GL600", 347, 358, 375, 371, 391, 411, 431, 435, 450, 459, 475, 536),
    ("8BP2GL700", 377, 406, 432, 407, 435, 433, 453, 473, 490, 526, 544, 616),
    ("8BP2GL800", 396, 428, 457, 431, 460, 495, 523, 530, 552, 548, 567, 638),
    ("8BP2GL900", 426, 461, 491, 477, 511, 517, 545, 552, 574, 591, 609, 679),
    ("8BP2GL1000", 448, 461, 490, 495, 532, 568, 605, 613, 642, 657, 671, 759),
    ("8BP2GL1200", 474, 485, 515, 519, 558, 593, 629, 637, 666, 683, 695, 784),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 2 caceroleros 400mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 159, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 puerta extraible BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1PEB600", 188, 193, 207, 213, 232, 242, 257, 261, 274, 273, 280, 317),
    ("8BP1PEB700", 212, 217, 231, 237, 256, 266, 281, 286, 298, 297, 305, 341),
    ("8BP1PEB800", 236, 242, 255, 261, 280, 290, 306, 310, 322, 321, 329, 365),
    ("8BP1PEB900", 260, 266, 279, 286, 305, 314, 330, 334, 347, 345, 353, 390),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 puerta extraible BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 159, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 puerta extraible LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BP1PEL600", 226, 230, 244, 250, 269, 278, 294, 298, 311, 311, 317, 354),
    ("8BP1PEL700", 255, 259, 273, 279, 298, 308, 323, 328, 340, 340, 347, 383),
    ("8BP1PEL800", 285, 289, 302, 309, 328, 337, 353, 357, 370, 370, 376, 413),
    ("8BP1PEL900", 314, 318, 332, 338, 357, 366, 382, 386, 399, 399, 405, 442),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo Placa 1 puerta extraible LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 159, "width": extract_width(ref), "height": 80, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 155-159")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
