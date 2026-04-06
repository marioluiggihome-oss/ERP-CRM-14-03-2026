#!/usr/bin/env python3
"""
Process pages 145-149 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS 80cm FONDO ESTÁNDAR
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
# PAGE 145 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1P300", 102, 106, 114, 111, 121, 148, 160, 163, 172, 175, 183, 221),
    ("8B1P350", 109, 112, 122, 120, 131, 156, 169, 172, 182, 196, 206, 229),
    ("8B1P400", 116, 120, 129, 129, 142, 161, 174, 177, 187, 192, 204, 237),
    ("8B1P450", 122, 126, 137, 139, 153, 171, 185, 189, 200, 201, 208, 246),
    ("8B1P500", 129, 133, 145, 148, 164, 182, 196, 201, 212, 210, 216, 254),
    ("8B1P600", 142, 147, 161, 167, 186, 194, 211, 214, 228, 227, 234, 271),
    ("8B1P650", 167, 173, 190, 197, 219, 229, 249, 253, 269, 268, 276, 320),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 145, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2P600", 168, 175, 192, 186, 204, 259, 284, 289, 308, 314, 329, 405),
    ("8B2P700", 182, 189, 207, 204, 226, 277, 302, 309, 329, 331, 356, 422),
    ("8B2P800", 194, 203, 223, 223, 248, 286, 312, 318, 338, 349, 371, 438),
    ("8B2P900", 210, 217, 239, 244, 271, 308, 420, 343, 365, 368, 382, 457),
    ("8B2P1000", 223, 232, 255, 261, 293, 329, 359, 366, 391, 384, 399, 474),
    ("8B2P1200", 249, 258, 286, 299, 420, 355, 386, 395, 420, 419, 433, 507),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 145, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1V300", 306, 286, 301, 296, 315, 343, 368, 373, 392, 398, 413, 489),
    ("8B1V350", 321, 306, 323, 321, 343, 368, 393, 399, 419, 421, 446, 512),
    ("8B1V400", 338, 324, 344, 347, 371, 382, 408, 415, 435, 445, 467, 534),
    ("8B1V450", 354, 344, 365, 371, 399, 408, 437, 444, 466, 468, 483, 558),
    ("8B1V500", 370, 364, 387, 396, 427, 436, 466, 474, 498, 491, 506, 581),
    ("8B1V600", 401, 403, 431, 445, 483, 474, 506, 513, 540, 539, 552, 626),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 145, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2V600", 277, 242, 258, 247, 266, 273, 294, 297, 313, 347, 366, 439),
    ("8B2V700", 296, 264, 282, 271, 292, 292, 311, 316, 332, 371, 390, 462),
    ("8B2V800", 314, 284, 303, 295, 319, 311, 332, 420, 353, 395, 414, 486),
    ("8B2V900", 332, 305, 328, 320, 347, 420, 359, 365, 383, 418, 437, 509),
    ("8B2V1000", 351, 328, 352, 345, 374, 363, 386, 393, 412, 442, 461, 531),
    ("8B2V1200", 384, 370, 398, 396, 431, 417, 446, 454, 477, 490, 508, 579),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 vitrinas",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 145, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 146 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta 640mm + 1 cajón 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1P1CB300", 145, 146, 155, 149, 160, 180, 191, 194, 203, 221, 231, 260),
    ("8B1P1CB350", 152, 154, 165, 158, 169, 185, 196, 200, 209, 230, 240, 269),
    ("8B1P1CB400", 161, 162, 173, 167, 180, 191, 204, 206, 215, 238, 249, 278),
    ("8B1P1CB450", 169, 170, 184, 176, 191, 203, 216, 219, 230, 248, 258, 287),
    ("8B1P1CB500", 176, 180, 193, 186, 202, 212, 226, 229, 240, 257, 268, 296),
    ("8B1P1CB600", 192, 195, 212, 206, 225, 231, 247, 251, 264, 275, 286, 313),
    ("8B1P1CB650", 227, 230, 250, 243, 265, 273, 291, 296, 311, 325, 421, 369),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta 640mm + 1 cajón 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 146, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta 640mm + 1 cajón 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1P1CL300", 179, 180, 190, 184, 194, 214, 226, 228, 237, 255, 266, 295),
    ("8B1P1CL350", 187, 188, 200, 192, 204, 219, 231, 234, 244, 265, 275, 303),
    ("8B1P1CL400", 195, 196, 208, 202, 214, 226, 237, 240, 250, 273, 284, 312),
    ("8B1P1CL450", 203, 205, 218, 211, 226, 237, 251, 254, 265, 282, 293, 321),
    ("8B1P1CL500", 211, 214, 228, 221, 236, 247, 260, 264, 275, 292, 301, 330),
    ("8B1P1CL600", 227, 230, 247, 240, 259, 266, 281, 286, 298, 310, 320, 348),
    ("8B1P1CL650", 268, 271, 291, 284, 306, 313, 332, 421, 352, 366, 378, 410),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 puerta 640mm + 1 cajón 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 146, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 640mm + 1 cajón 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2P1CB600", 218, 224, 243, 227, 246, 274, 293, 298, 314, 349, 368, 426),
    ("8B2P1CB700", 236, 243, 264, 250, 273, 297, 319, 324, 342, 384, 415, 462),
    ("8B2P1CB800", 253, 258, 281, 268, 294, 317, 341, 347, 366, 408, 433, 486),
    ("8B2P1CB900", 271, 277, 303, 290, 318, 342, 369, 375, 396, 433, 453, 509),
    ("8B2P1CB1000", 290, 295, 323, 309, 340, 360, 389, 395, 417, 450, 470, 528),
    ("8B2P1CB1200", 321, 328, 360, 347, 384, 398, 429, 437, 462, 487, 506, 563),
    ("8B2P1CB1300", 369, 377, 414, 398, 442, 458, 494, 502, 531, 560, 582, 647),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 146, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 147 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 2 puertas 640mm + 1 cajón 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B2P1CL600", 253, 258, 276, 261, 280, 309, 328, 333, 349, 383, 401, 461),
    ("8B2P1CL700", 271, 277, 298, 285, 308, 332, 354, 359, 377, 419, 449, 497),
    ("8B2P1CL800", 288, 293, 316, 302, 329, 352, 376, 381, 401, 443, 467, 521),
    ("8B2P1CL900", 306, 312, 338, 324, 354, 377, 403, 410, 431, 467, 487, 544),
    ("8B2P1CL1000", 324, 330, 358, 343, 375, 395, 423, 429, 452, 485, 506, 563),
    ("8B2P1CL1200", 356, 362, 395, 382, 420, 433, 464, 473, 498, 522, 542, 597),
    ("8B2P1CL1300", 409, 417, 454, 440, 483, 497, 534, 543, 572, 600, 623, 687),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 147, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 4 cajones 200mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B4CB300", 238, 245, 259, 277, 300, 343, 369, 375, 394, 471, 499, 602),
    ("8B4CB350", 250, 257, 274, 292, 317, 356, 382, 389, 410, 503, 532, 645),
    ("8B4CB400", 261, 271, 289, 307, 334, 362, 389, 395, 415, 508, 539, 651),
    ("8B4CB450", 273, 284, 303, 323, 353, 375, 402, 408, 431, 540, 572, 693),
    ("8B4CB500", 285, 297, 318, 339, 372, 381, 408, 415, 436, 546, 578, 699),
    ("8B4CB600", 308, 323, 349, 366, 403, 393, 420, 426, 448, 558, 590, 711),
    ("8B4CB700", 331, 349, 377, 386, 424, 434, 465, 474, 498, 721, 758, 941),
    ("8B4CB800", 354, 374, 405, 420, 464, 498, 538, 547, 579, 733, 770, 952),
    ("8B4CB900", 379, 401, 437, 457, 506, 564, 611, 624, 662, 748, 784, 967),
    ("8B4CB1000", 421, 446, 489, 530, 595, 652, 712, 727, 774, 944, 1008, 1251),
    ("8B4CB1200", 466, 498, 548, 585, 657, 751, 822, 840, 896, 967, 1031, 1274),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 4 cajones 200mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 147, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 4 cajones 200mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B4CL300", 379, 385, 400, 418, 441, 484, 509, 516, 534, 612, 639, 742),
    ("8B4CL350", 391, 399, 415, 433, 458, 498, 523, 529, 550, 644, 673, 785),
    ("8B4CL400", 402, 412, 429, 447, 475, 503, 529, 536, 555, 650, 679, 792),
    ("8B4CL450", 414, 424, 444, 464, 494, 517, 543, 550, 571, 681, 713, 835),
    ("8B4CL500", 425, 438, 460, 481, 512, 522, 549, 555, 578, 687, 719, 840),
    ("8B4CL600", 449, 465, 489, 508, 544, 534, 562, 568, 589, 699, 732, 853),
    ("8B4CL700", 473, 490, 519, 528, 566, 575, 607, 615, 639, 863, 900, 1083),
    ("8B4CL800", 496, 516, 548, 562, 606, 639, 679, 689, 720, 875, 911, 1095),
    ("8B4CL900", 521, 544, 579, 599, 648, 706, 754, 765, 803, 889, 926, 1109),
    ("8B4CL1000", 563, 588, 631, 673, 737, 794, 854, 868, 916, 1086, 1150, 1392),
    ("8B4CL1200", 609, 641, 691, 728, 800, 894, 965, 983, 1040, 1110, 1174, 1416),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 4 cajones 200mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 147, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 148 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 5 cajones 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B5CB300", 278, 268, 280, 275, 290, 331, 348, 353, 366, 385, 398, 391),
    ("8B5CB350", 291, 281, 296, 287, 301, 337, 355, 359, 373, 397, 408, 402),
    ("8B5CB400", 303, 295, 311, 298, 314, 343, 361, 365, 379, 408, 420, 414),
    ("8B5CB450", 316, 308, 326, 309, 327, 363, 383, 387, 403, 420, 432, 425),
    ("8B5CB500", 329, 321, 340, 320, 339, 370, 390, 394, 410, 432, 443, 437),
    ("8B5CB600", 354, 348, 370, 343, 364, 383, 403, 407, 423, 455, 466, 459),
    ("8B5CB700", 386, 385, 414, 395, 425, 459, 488, 496, 519, 567, 639, 573),
    ("8B5CB800", 418, 412, 442, 417, 450, 509, 545, 553, 581, 620, 662, 626),
    ("8B5CB900", 443, 439, 474, 441, 477, 550, 589, 599, 630, 664, 687, 673),
    ("8B5CB1000", 481, 466, 504, 464, 502, 563, 603, 612, 643, 687, 711, 696),
    ("8B5CB1200", 530, 518, 562, 509, 551, 590, 629, 638, 669, 733, 756, 741),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 5 cajones 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 148, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 5 cajones 200mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B5CL300", 455, 444, 457, 452, 465, 506, 524, 528, 543, 561, 573, 567),
    ("8B5CL350", 467, 458, 473, 463, 478, 513, 531, 536, 549, 573, 585, 579),
    ("8B5CL400", 480, 471, 487, 475, 490, 520, 538, 542, 555, 585, 596, 590),
    ("8B5CL450", 492, 485, 502, 486, 503, 540, 560, 564, 580, 596, 608, 602),
    ("8B5CL500", 505, 498, 517, 497, 516, 547, 566, 571, 586, 608, 621, 613),
    ("8B5CL600", 531, 525, 546, 520, 542, 561, 580, 585, 601, 632, 644, 636),
    ("8B5CL700", 564, 563, 591, 572, 603, 636, 666, 673, 696, 744, 817, 751),
    ("8B5CL800", 596, 589, 620, 595, 628, 687, 722, 731, 759, 797, 840, 804),
    ("8B5CL900", 622, 617, 652, 620, 655, 728, 768, 776, 807, 841, 865, 852),
    ("8B5CL1000", 659, 645, 683, 643, 680, 741, 781, 790, 821, 865, 888, 875),
    ("8B5CL1200", 710, 697, 741, 688, 731, 769, 807, 817, 848, 912, 936, 921),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 5 cajones 200mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 148, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 149 - BAJOS 80cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 cacerolero 320mm + 3 cajones 160mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G3CB300", 250, 246, 257, 257, 271, 307, 324, 328, 341, 371, 385, 407),
    ("8B1G3CB350", 261, 257, 270, 268, 284, 316, 333, 337, 351, 386, 401, 425),
    ("8B1G3CB400", 273, 269, 284, 279, 296, 321, 339, 343, 357, 395, 410, 434),
    ("8B1G3CB450", 284, 281, 297, 291, 310, 338, 357, 362, 377, 411, 426, 453),
    ("8B1G3CB500", 295, 293, 311, 302, 322, 344, 363, 368, 382, 420, 435, 461),
    ("8B1G3CB600", 318, 317, 337, 327, 350, 356, 375, 380, 395, 438, 453, 479),
    ("8B1G3CB700", 344, 348, 372, 364, 394, 412, 437, 443, 464, 553, 611, 611),
    ("8B1G3CB800", 371, 371, 398, 389, 421, 461, 492, 500, 525, 588, 629, 647),
    ("8B1G3CB900", 394, 396, 426, 414, 448, 505, 542, 550, 579, 620, 649, 680),
    ("8B1G3CB1000", 434, 432, 467, 443, 482, 549, 590, 601, 633, 660, 681, 717),
    ("8B1G3CB1200", 473, 470, 510, 478, 520, 572, 614, 624, 657, 696, 717, 753),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 320mm + 3 cajones 160mm BAX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 149, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 320mm + 3 cajones 160mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8B1G3CL300", 394, 389, 400, 400, 415, 450, 467, 471, 485, 515, 529, 551),
    ("8B1G3CL350", 405, 401, 414, 412, 427, 459, 477, 481, 495, 530, 545, 569),
    ("8B1G3CL400", 417, 413, 427, 423, 440, 465, 483, 487, 501, 539, 553, 578),
    ("8B1G3CL450", 427, 425, 441, 435, 454, 482, 501, 505, 521, 554, 570, 596),
    ("8B1G3CL500", 439, 437, 455, 446, 466, 488, 507, 511, 526, 564, 579, 605),
    ("8B1G3CL600", 462, 461, 481, 470, 494, 500, 519, 524, 539, 582, 596, 623),
    ("8B1G3CL700", 488, 491, 516, 508, 538, 555, 582, 587, 608, 697, 755, 755),
    ("8B1G3CL800", 516, 515, 543, 533, 566, 605, 636, 644, 669, 733, 773, 792),
    ("8B1G3CL900", 539, 541, 571, 558, 593, 649, 686, 694, 723, 764, 793, 824),
    ("8B1G3CL1000", 579, 575, 612, 587, 626, 693, 733, 744, 777, 804, 825, 862),
    ("8B1G3CL1200", 616, 615, 655, 623, 665, 717, 759, 769, 801, 841, 861, 897),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo 1 cacerolero 320mm + 3 cajones 160mm LUX",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm FONDO ESTÁNDAR",
        "sourcePage": 149, "width": extract_width(ref), "height": 80, "depth": 58,
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
print(f"RESUMEN - PÁGINAS 145-149")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
