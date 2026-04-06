#!/usr/bin/env python3
"""
Process pages 130-134 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS - BAJOS 70cm FONDO ESTÁNDAR + BAJOS 70cm fondo 33cm
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
# PAGE 130 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo Fregadero 1 puerta extraíble LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF1PEL450", 189, 192, 202, 198, 209, 214, 223, 226, 233, 248, 255, 286),
    ("7BF1PEL500", 196, 201, 211, 208, 219, 224, 234, 236, 244, 258, 264, 294),
    ("7BF1PEL600", 211, 215, 227, 226, 240, 244, 256, 258, 268, 273, 281, 311),
    ("7BF1PEL700", 226, 230, 243, 242, 257, 260, 273, 276, 287, 292, 301, 333),
    ("7BF1PEL800", 242, 247, 259, 258, 275, 279, 292, 296, 307, 313, 322, 356),
    ("7BF1PEL900", 258, 264, 278, 276, 295, 298, 313, 316, 328, 335, 344, 381),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 1 puerta extraíble LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 130,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BFRA930", 313, 319, 335, 324, 342, 359, 375, 379, 393, 425, 441, 502),
    ("7BFRA1030", 358, 365, 384, 377, 399, 407, 426, 431, 445, 476, 490, 551),
    ("7BFRA1080", 375, 383, 403, 397, 421, 428, 449, 454, 470, 495, 510, 570),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero rincón angular 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 130,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BFRL1P900", 148, 153, 161, 152, 163, 174, 185, 184, 192, 221, 230, 259),
    ("7BFRL1P950", 153, 158, 165, 156, 167, 179, 189, 189, 196, 225, 234, 264),
    ("7BFRL1P1000", 155, 161, 169, 161, 172, 181, 191, 191, 198, 230, 238, 268),
    ("7BFRL1P1050", 168, 172, 181, 174, 186, 192, 203, 203, 210, 243, 251, 280),
    ("7BFRL1P1100", 171, 175, 185, 179, 192, 196, 208, 208, 217, 247, 255, 285),
    ("7BFRL1P1150", 173, 180, 190, 184, 198, 202, 214, 214, 224, 251, 259, 289),
    ("7BFRL1P1200", 180, 186, 197, 193, 211, 213, 228, 229, 239, 260, 268, 297),
    ("7BFRL1P1250", 188, 193, 205, 202, 218, 222, 236, 236, 247, 268, 275, 305),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero rincón lineal 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 130,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero rincón lineal 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BFRL2P1200", 215, 224, 237, 225, 243, 266, 284, 286, 299, 342, 359, 420),
    ("7BFRL2P1400", 237, 246, 263, 251, 273, 285, 303, 306, 320, 370, 386, 446),
    ("7BFRL2P1500", 248, 257, 276, 266, 291, 299, 320, 322, 338, 383, 399, 459),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero rincón lineal 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 130,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 131 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1P600", 163, 168, 180, 179, 193, 195, 208, 210, 219, 226, 233, 263),
    ("7BP1P650", 176, 181, 194, 193, 209, 211, 225, 227, 237, 244, 252, 284),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 131,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP2P600", 189, 195, 209, 200, 214, 238, 254, 258, 270, 298, 315, 376),
    ("7BP2P700", 207, 213, 229, 219, 236, 253, 270, 274, 287, 319, 335, 396),
    ("7BP2P800", 223, 229, 246, 237, 257, 268, 285, 289, 302, 337, 353, 414),
    ("7BP2P900", 240, 248, 267, 259, 281, 291, 309, 314, 329, 358, 374, 434),
    ("7BP2P1000", 257, 266, 287, 280, 305, 311, 332, 337, 353, 378, 393, 453),
    ("7BP2P1200", 288, 297, 321, 318, 348, 353, 377, 382, 402, 414, 428, 487),
    ("7BP2P1300", 314, 324, 350, 347, 379, 385, 411, 417, 438, 451, 467, 531),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 131,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 280mm + 3 cajones 140mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1G3CB600", 340, 340, 360, 349, 371, 379, 398, 402, 417, 464, 479, 504),
    ("7BP1G3CB700", 372, 376, 400, 391, 419, 442, 467, 474, 494, 579, 631, 637),
    ("7BP1G3CB800", 402, 402, 429, 418, 448, 492, 524, 531, 555, 617, 652, 676),
    ("7BP1G3CB900", 428, 432, 461, 447, 481, 539, 574, 583, 611, 653, 676, 714),
    ("7BP1G3CB1000", 467, 464, 498, 484, 523, 574, 613, 622, 652, 721, 752, 803),
    ("7BP1G3CB1200", 517, 518, 557, 533, 578, 624, 665, 675, 708, 763, 794, 845),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 cacerolero 280mm + 3 cajones 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 131,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 280mm + 3 cajones 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1G3CL600", 485, 485, 505, 494, 516, 524, 543, 547, 562, 609, 624, 650),
    ("7BP1G3CL700", 518, 521, 545, 537, 564, 587, 612, 618, 638, 723, 776, 782),
    ("7BP1G3CL800", 547, 548, 574, 563, 593, 637, 669, 676, 700, 762, 797, 821),
    ("7BP1G3CL900", 573, 578, 607, 592, 626, 684, 719, 728, 756, 798, 821, 859),
    ("7BP1G3CL1000", 612, 610, 644, 630, 669, 719, 758, 768, 798, 866, 897, 949),
    ("7BP1G3CL1200", 663, 663, 701, 679, 722, 769, 811, 820, 853, 909, 940, 991),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 cacerolero 280mm + 3 cajones 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 131,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 132 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 2 caceroleros 280mm + 1 cajón 140mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP2G1CB600", 300, 307, 323, 328, 350, 349, 366, 371, 384, 446, 464, 523),
    ("7BP2G1CB700", 327, 327, 355, 356, 381, 419, 437, 495, 474, 558, 591, 669),
    ("7BP2G1CB800", 350, 358, 380, 382, 412, 440, 467, 474, 495, 580, 607, 691),
    ("7BP2G1CB900", 374, 384, 410, 413, 444, 488, 520, 527, 552, 603, 626, 714),
    ("7BP2G1CB1000", 410, 419, 448, 461, 501, 541, 579, 588, 618, 712, 749, 867),
    ("7BP2G1CB1200", 453, 506, 500, 507, 552, 607, 650, 660, 695, 743, 780, 899),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 2 caceroleros 280mm + 1 cajón 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 132,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 caceroleros 280mm + 1 cajón 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP2G1CL600", 413, 419, 436, 440, 462, 461, 478, 483, 497, 558, 576, 635),
    ("7BP2G1CL700", 438, 446, 466, 467, 492, 504, 526, 531, 548, 670, 702, 780),
    ("7BP2G1CL800", 461, 470, 492, 495, 523, 551, 579, 585, 606, 691, 718, 802),
    ("7BP2G1CL900", 485, 497, 521, 524, 555, 600, 631, 639, 664, 714, 737, 825),
    ("7BP2G1CL1000", 521, 530, 560, 572, 612, 652, 690, 699, 730, 823, 860, 979),
    ("7BP2G1CL1200", 564, 578, 611, 618, 664, 718, 761, 772, 806, 855, 891, 1010),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 2 caceroleros 280mm + 1 cajón 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 132,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 350mm + 2 cajones 175mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1G2CB600", 288, 289, 305, 299, 318, 320, 420, 339, 352, 389, 401, 428),
    ("7BP1G2CB700", 315, 318, 337, 334, 357, 368, 387, 393, 408, 488, 531, 545),
    ("7BP1G2CB800", 340, 341, 362, 358, 384, 412, 436, 442, 462, 518, 549, 574),
    ("7BP1G2CB900", 364, 366, 391, 384, 412, 454, 482, 489, 511, 546, 570, 604),
    ("7BP1G2CB1000", 402, 402, 431, 414, 446, 501, 534, 542, 569, 587, 603, 643),
    ("7BP1G2CB1200", 439, 440, 471, 449, 483, 528, 562, 570, 597, 623, 638, 677),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 cacerolero 350mm + 2 cajones 175mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 132,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 cacerolero 350mm + 2 cajones 175mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1G2CL600", 398, 398, 414, 408, 427, 431, 445, 448, 461, 498, 510, 538),
    ("7BP1G2CL700", 424, 427, 447, 443, 466, 477, 497, 502, 518, 597, 641, 654),
    ("7BP1G2CL800", 449, 450, 473, 467, 494, 521, 546, 551, 571, 627, 658, 684),
    ("7BP1G2CL900", 474, 477, 500, 494, 521, 563, 591, 599, 621, 655, 679, 714),
    ("7BP1G2CL1000", 511, 512, 541, 524, 555, 610, 643, 652, 678, 696, 713, 752),
    ("7BP1G2CL1200", 549, 549, 581, 559, 592, 637, 671, 679, 706, 732, 748, 786),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 cacerolero 350mm + 2 cajones 175mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 132,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 133 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo Placa 2 caceroleros 350mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP2GB600", 252, 257, 272, 282, 302, 294, 308, 312, 323, 371, 387, 447),
    ("7BP2GB700", 274, 280, 296, 303, 326, 320, 354, 358, 370, 474, 503, 583),
    ("7BP2GB800", 293, 301, 318, 330, 355, 362, 384, 389, 405, 486, 516, 595),
    ("7BP2GB900", 315, 323, 343, 356, 383, 408, 434, 440, 461, 502, 531, 611),
    ("7BP2GB1000", 356, 368, 395, 393, 426, 486, 522, 531, 559, 561, 574, 664),
    ("7BP2GB1200", 380, 393, 419, 417, 450, 510, 546, 555, 584, 586, 599, 688),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 2 caceroleros 350mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 133,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 2 caceroleros 350mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP2GL600", 329, 334, 348, 359, 379, 370, 384, 387, 399, 447, 463, 524),
    ("7BP2GL700", 350, 356, 372, 379, 401, 396, 413, 417, 429, 550, 580, 659),
    ("7BP2GL800", 369, 377, 395, 406, 432, 439, 460, 465, 482, 563, 592, 671),
    ("7BP2GL900", 391, 399, 419, 432, 459, 484, 510, 517, 537, 578, 607, 687),
    ("7BP2GL1000", 432, 443, 470, 468, 502, 562, 597, 606, 634, 636, 649, 739),
    ("7BP2GL1200", 456, 467, 495, 492, 526, 586, 622, 630, 659, 660, 674, 763),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 2 caceroleros 350mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 133,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 puerta extraíble BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1PEB600", 166, 170, 182, 181, 195, 197, 210, 213, 223, 228, 235, 266),
    ("7BP1PEB700", 181, 185, 197, 196, 212, 214, 228, 232, 242, 248, 255, 289),
    ("7BP1PEB800", 196, 202, 214, 213, 231, 233, 248, 251, 263, 269, 277, 313),
    ("7BP1PEB900", 213, 218, 233, 232, 250, 253, 269, 273, 285, 292, 300, 339),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 puerta extraíble BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 133,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Placa 1 puerta extraíble LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BP1PEL600", 211, 215, 227, 226, 240, 244, 255, 258, 268, 273, 281, 311),
    ("7BP1PEL700", 226, 230, 243, 242, 257, 260, 273, 276, 287, 292, 301, 333),
    ("7BP1PEL800", 242, 247, 259, 258, 275, 279, 292, 296, 307, 313, 322, 356),
    ("7BP1PEL900", 258, 264, 278, 276, 295, 298, 313, 316, 328, 335, 344, 381),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Placa 1 puerta extraíble LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 133,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 134 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 frente horno 600mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BPH600", 89, 88, 92, 87, 91, 96, 99, 100, 103, 109, 111, 110),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 frente horno 600mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 134,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 250 BAX + horno 450mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BPH451GB600", 140, 144, 150, 154, 164, 161, 168, 169, 174, 203, 210, 240),
    ("7BPH451GB900", 173, 179, 187, 192, 205, 219, 231, 234, 244, 265, 274, 320),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 250 BAX + horno 450mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 134,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 250 LUX + horno 450mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BPH451GL600", 177, 182, 188, 192, 202, 200, 206, 208, 213, 240, 248, 278),
    ("7BPH451GL900", 211, 216, 225, 230, 243, 257, 269, 272, 281, 302, 312, 358),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 250 LUX + horno 450mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 134,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 134 - BAJOS DE 70cm fondo 33cm
# ============================================

# Bajo 1 puerta fondo 330 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1PX300", 82, 85, 91, 86, 95, 106, 114, 116, 122, 137, 145, 175),
    ("7B1PX350", 87, 90, 99, 93, 102, 110, 119, 121, 127, 143, 151, 182),
    ("7B1PX400", 92, 96, 104, 100, 110, 116, 124, 126, 132, 150, 158, 188),
    ("7B1PX450", 99, 102, 111, 108, 119, 123, 132, 134, 142, 158, 165, 194),
    ("7B1PX500", 104, 108, 119, 116, 127, 131, 141, 144, 151, 164, 172, 202),
    ("7B1PX600", 116, 120, 131, 130, 145, 147, 160, 163, 172, 177, 185, 215),
    ("7B1PX650", 139, 144, 158, 156, 174, 176, 192, 195, 207, 213, 222, 258),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta fondo 330",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 134,
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
print(f"RESUMEN - PÁGINAS 130-134")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias añadidas: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
print(f"{'='*50}")

if new_refs:
    print(f"\nNuevas referencias añadidas (primeras 30):")
    for ref in sorted(new_refs)[:30]:
        print(f"  - {ref}")
    if len(new_refs) > 30:
        print(f"  ... y {len(new_refs) - 30} más")
