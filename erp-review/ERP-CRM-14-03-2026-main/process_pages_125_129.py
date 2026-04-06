#!/usr/bin/env python3
"""
Process pages 125-129 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS - BAJOS 70cm FONDO ESTÁNDAR
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
# PAGE 125 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2G1CB300", 212, 213, 224, 231, 246, 275, 291, 295, 308, 351, 366, 417),
    ("7B2G1CB350", 222, 224, 234, 242, 257, 284, 300, 305, 317, 369, 386, 441),
    ("7B2G1CB400", 231, 233, 246, 252, 269, 289, 306, 310, 322, 394, 413, 447),
    ("7B2G1CB450", 239, 244, 256, 264, 281, 300, 317, 321, 420, 413, 471, 471),
    ("7B2G1CB500", 249, 254, 268, 275, 295, 306, 322, 328, 341, 400, 419, 478),
    ("7B2G1CB600", 267, 274, 291, 295, 317, 316, 333, 337, 351, 413, 431, 490),
    ("7B2G1CB700", 288, 296, 316, 317, 342, 354, 375, 380, 398, 519, 551, 630),
    ("7B2G1CB800", 307, 316, 338, 340, 369, 397, 424, 431, 453, 537, 564, 648),
    ("7B2G1CB900", 327, 337, 362, 365, 397, 441, 473, 480, 505, 555, 579, 667),
    ("7B2G1CB1000", 357, 368, 396, 408, 448, 489, 527, 537, 566, 660, 697, 816),
    ("7B2G1CB1200", 394, 407, 441, 449, 494, 548, 592, 603, 636, 686, 721, 840),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 125,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 280mm + 1 cajón 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2G1CL300", 324, 326, 335, 343, 358, 387, 403, 407, 420, 462, 479, 528),
    ("7B2G1CL350", 333, 335, 347, 354, 369, 396, 413, 416, 429, 481, 498, 553),
    ("7B2G1CL400", 342, 345, 357, 364, 381, 401, 418, 421, 435, 487, 504, 559),
    ("7B2G1CL450", 352, 355, 369, 375, 394, 412, 429, 434, 447, 506, 524, 584),
    ("7B2G1CL500", 361, 365, 380, 386, 406, 417, 435, 439, 453, 512, 530, 590),
    ("7B2G1CL600", 379, 385, 402, 406, 428, 427, 445, 449, 463, 524, 543, 602),
    ("7B2G1CL700", 399, 407, 427, 428, 454, 465, 487, 492, 509, 630, 664, 741),
    ("7B2G1CL800", 419, 427, 449, 452, 480, 509, 536, 543, 564, 649, 675, 760),
    ("7B2G1CL900", 439, 449, 474, 477, 509, 552, 584, 592, 617, 667, 690, 778),
    ("7B2G1CL1000", 468, 479, 507, 521, 561, 601, 638, 648, 677, 772, 809, 927),
    ("7B2G1CL1200", 505, 519, 552, 561, 605, 659, 704, 714, 748, 796, 833, 951),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 125,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G2CB300", 201, 198, 207, 208, 219, 247, 260, 264, 275, 300, 312, 335),
    ("7B1G2CB350", 210, 208, 218, 217, 230, 255, 269, 272, 284, 314, 327, 352),
    ("7B1G2CB400", 219, 217, 229, 227, 240, 260, 274, 277, 289, 321, 333, 359),
    ("7B1G2CB450", 229, 227, 239, 237, 252, 273, 288, 292, 303, 335, 348, 375),
    ("7B1G2CB500", 237, 237, 251, 247, 264, 278, 293, 297, 309, 341, 355, 382),
    ("7B1G2CB600", 256, 256, 272, 267, 286, 289, 303, 308, 319, 356, 369, 396),
    ("7B1G2CB700", 277, 280, 299, 296, 319, 330, 350, 355, 371, 449, 494, 507),
    ("7B1G2CB800", 298, 299, 321, 317, 342, 370, 395, 401, 420, 476, 507, 533),
    ("7B1G2CB900", 318, 321, 344, 338, 365, 407, 436, 443, 465, 500, 524, 558),
    ("7B1G2CB1000", 352, 352, 380, 363, 395, 449, 483, 491, 518, 537, 552, 591),
    ("7B1G2CB1200", 382, 382, 414, 392, 425, 470, 504, 512, 539, 565, 581, 620),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 125,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 126 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G2CL300", 309, 307, 315, 316, 328, 355, 369, 372, 383, 408, 420, 443),
    ("7B1G2CL350", 318, 316, 327, 326, 338, 363, 377, 380, 392, 422, 435, 460),
    ("7B1G2CL400", 328, 326, 337, 335, 349, 369, 382, 385, 397, 429, 441, 467),
    ("7B1G2CL450", 337, 335, 348, 345, 360, 381, 397, 400, 412, 443, 456, 483),
    ("7B1G2CL500", 345, 345, 359, 355, 372, 386, 402, 405, 417, 450, 463, 490),
    ("7B1G2CL600", 364, 364, 380, 375, 394, 397, 412, 416, 427, 464, 477, 504),
    ("7B1G2CL700", 385, 389, 407, 404, 427, 438, 458, 463, 479, 559, 602, 615),
    ("7B1G2CL800", 407, 408, 429, 425, 452, 479, 503, 509, 528, 584, 616, 642),
    ("7B1G2CL900", 426, 429, 453, 446, 475, 516, 544, 551, 573, 608, 632, 667),
    ("7B1G2CL1000", 460, 460, 488, 471, 504, 559, 592, 600, 627, 645, 660, 700),
    ("7B1G2CL1200", 490, 491, 522, 500, 533, 580, 613, 621, 648, 674, 690, 729),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 126,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 350mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2GB300", 172, 174, 183, 189, 201, 223, 235, 238, 249, 286, 299, 351),
    ("7B2GB350", 180, 183, 191, 197, 211, 232, 246, 250, 260, 302, 317, 374),
    ("7B2GB400", 188, 191, 201, 208, 222, 237, 251, 254, 265, 308, 322, 378),
    ("7B2GB450", 195, 200, 210, 217, 233, 247, 261, 265, 276, 324, 340, 401),
    ("7B2GB500", 203, 208, 219, 229, 246, 251, 266, 270, 281, 329, 344, 405),
    ("7B2GB600", 218, 225, 238, 249, 270, 260, 275, 278, 290, 338, 354, 415),
    ("7B2GB700", 234, 242, 257, 265, 286, 281, 297, 301, 314, 435, 464, 544),
    ("7B2GB800", 250, 258, 276, 288, 313, 320, 341, 347, 363, 444, 474, 553),
    ("7B2GB900", 268, 276, 296, 309, 420, 361, 387, 394, 414, 455, 484, 564),
    ("7B2GB1000", 303, 316, 342, 340, 374, 435, 470, 479, 507, 509, 522, 612),
    ("7B2GB1200", 322, 334, 361, 359, 393, 453, 488, 497, 525, 527, 541, 630),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 caceroleros 350mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 126,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 caceroleros 350mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2GL300", 249, 251, 259, 266, 277, 299, 312, 315, 326, 362, 376, 427),
    ("7B2GL350", 256, 259, 268, 274, 288, 309, 322, 327, 337, 379, 394, 450),
    ("7B2GL400", 264, 268, 277, 285, 298, 314, 328, 331, 341, 383, 399, 455),
    ("7B2GL450", 272, 275, 287, 294, 310, 323, 338, 341, 353, 401, 417, 478),
    ("7B2GL500", 279, 285, 296, 305, 322, 328, 342, 345, 357, 405, 421, 482),
    ("7B2GL600", 295, 300, 315, 326, 345, 337, 351, 355, 366, 414, 431, 490),
    ("7B2GL700", 311, 317, 333, 340, 362, 357, 374, 378, 391, 511, 541, 620),
    ("7B2GL800", 327, 334, 352, 363, 389, 396, 417, 422, 439, 520, 549, 629),
    ("7B2GL900", 343, 353, 372, 384, 413, 437, 463, 469, 489, 530, 560, 639),
    ("7B2GL1000", 379, 392, 418, 416, 449, 510, 546, 554, 583, 585, 597, 688),
    ("7B2GL1200", 397, 410, 436, 434, 467, 528, 564, 572, 601, 603, 615, 705),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 caceroleros 350mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 126,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 127 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta extraíble BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1PEB450", 154, 158, 166, 163, 173, 173, 182, 183, 189, 197, 204, 227),
    ("7B1PEB500", 161, 164, 173, 170, 182, 181, 190, 192, 198, 204, 210, 234),
    ("7B1PEB600", 172, 176, 187, 186, 200, 197, 207, 210, 217, 217, 224, 247),
    ("7B1PEB650", 192, 196, 207, 206, 219, 217, 227, 230, 237, 237, 244, 267),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta extraíble BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 127,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta extraíble LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1PEL450", 189, 192, 203, 200, 211, 211, 221, 223, 230, 238, 246, 273),
    ("7B1PEL500", 196, 201, 211, 208, 221, 221, 230, 232, 240, 247, 254, 281),
    ("7B1PEL600", 210, 215, 227, 226, 242, 238, 251, 253, 263, 263, 269, 296),
    ("7B1PEL650", 229, 234, 246, 245, 260, 257, 270, 272, 281, 281, 288, 315),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta extraíble LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 127,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón angular 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BRA930", 264, 271, 287, 276, 294, 311, 327, 331, 343, 376, 393, 453),
    ("7BRA1030", 297, 305, 323, 316, 338, 348, 365, 371, 385, 415, 431, 490),
    ("7BRA1080", 314, 322, 343, 337, 361, 369, 389, 394, 410, 435, 449, 509),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo rincón angular 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 127,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón angular 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BRA1P930", 219, 227, 243, 232, 250, 267, 282, 287, 299, 332, 349, 408),
    ("7BRA2P1030", 253, 260, 279, 272, 294, 303, 321, 327, 341, 371, 386, 446),
    ("7BRA2P1080", 270, 278, 299, 293, 317, 324, 344, 350, 365, 391, 405, 465),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo rincón angular 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 127,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 128 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo rincón lineal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BRL1P900", 165, 170, 176, 169, 180, 191, 201, 201, 208, 237, 246, 276),
    ("7BRL1P1030", 168, 172, 180, 172, 182, 194, 204, 204, 211, 240, 249, 279),
    ("7BRL1P1000", 174, 179, 187, 179, 190, 198, 209, 209, 216, 248, 256, 286),
    ("7BRL1P1050", 181, 185, 193, 186, 198, 204, 215, 215, 223, 255, 264, 293),
    ("7BRL1P1100", 185, 190, 200, 193, 207, 211, 223, 223, 231, 260, 269, 298),
    ("7BRL1P1150", 191, 196, 207, 202, 216, 219, 232, 232, 242, 269, 277, 307),
    ("7BRL1P1200", 201, 207, 218, 215, 232, 235, 249, 250, 260, 281, 289, 318),
    ("7BRL1P1250", 209, 215, 227, 223, 240, 243, 257, 257, 269, 289, 297, 327),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo rincón lineal 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 128,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo rincón lineal 2 puertas (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BRL2P1200", 236, 245, 258, 246, 264, 288, 306, 307, 320, 364, 381, 441),
    ("7BRL2P1400", 266, 273, 290, 279, 301, 312, 332, 334, 349, 398, 414, 474),
    ("7BRL2P1500", 279, 289, 308, 297, 322, 331, 352, 354, 371, 415, 431, 490),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo rincón lineal 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 128,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo terminal 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BTER1P300", 133, 138, 145, 140, 149, 158, 165, 167, 173, 190, 198, 228),
    ("7BTER1P350", 143, 146, 155, 152, 163, 168, 176, 180, 187, 202, 209, 239),
    ("7BTER1P400", 146, 149, 159, 155, 166, 170, 180, 183, 190, 205, 212, 243),
    ("7BTER1P450", 151, 155, 166, 163, 175, 179, 189, 191, 200, 212, 219, 249),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo terminal 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 128,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF1P450", 121, 125, 134, 130, 142, 146, 155, 158, 165, 180, 188, 217),
    ("7BF1P500", 128, 132, 143, 139, 151, 154, 165, 167, 175, 188, 195, 226),
    ("7BF1P600", 141, 146, 158, 156, 170, 173, 185, 188, 197, 204, 211, 240),
    ("7BF1P650", 156, 162, 173, 172, 186, 189, 201, 204, 213, 219, 227, 256),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 128,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 129 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo Fregadero 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF2P600", 167, 173, 187, 176, 192, 216, 232, 236, 248, 236, 248, 354),
    ("7BF2P700", 180, 187, 203, 192, 210, 247, 256, 260, 274, 259, 292, 369),
    ("7BF2P800", 193, 200, 217, 209, 228, 239, 256, 260, 274, 309, 324, 384),
    ("7BF2P900", 210, 217, 236, 229, 251, 259, 278, 282, 297, 328, 342, 402),
    ("7BF2P1000", 224, 232, 253, 246, 271, 277, 298, 302, 319, 343, 359, 419),
    ("7BF2P1200", 251, 260, 284, 281, 309, 315, 340, 345, 364, 377, 392, 450),
    ("7BF2P1300", 273, 282, 306, 303, 333, 338, 362, 368, 386, 399, 414, 473),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 129,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 2 caceroleros BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF2GB600", 227, 233, 247, 257, 277, 269, 282, 287, 298, 345, 362, 422),
    ("7BF2GB700", 244, 251, 267, 273, 295, 290, 307, 311, 323, 444, 474, 553),
    ("7BF2GB800", 261, 269, 287, 298, 323, 331, 352, 357, 374, 455, 484, 564),
    ("7BF2GB900", 280, 290, 309, 321, 350, 374, 400, 406, 426, 468, 498, 576),
    ("7BF2GB1000", 318, 331, 358, 356, 389, 449, 485, 494, 522, 524, 537, 627),
    ("7BF2GB1200", 340, 353, 379, 377, 411, 471, 507, 516, 544, 545, 559, 648),
    ("7BF2GB1300", 373, 385, 412, 410, 443, 504, 540, 548, 576, 578, 591, 680),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 2 caceroleros BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 129,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 2 caceroleros LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF2GL600", 318, 323, 337, 349, 369, 359, 374, 377, 389, 437, 453, 513),
    ("7BF2GL700", 334, 341, 357, 364, 386, 381, 397, 401, 414, 534, 564, 644),
    ("7BF2GL800", 352, 360, 377, 389, 414, 421, 443, 447, 464, 545, 574, 654),
    ("7BF2GL900", 372, 380, 400, 412, 440, 465, 490, 497, 517, 559, 588, 667),
    ("7BF2GL1000", 408, 421, 448, 445, 479, 540, 575, 584, 612, 614, 627, 717),
    ("7BF2GL1200", 431, 442, 469, 467, 501, 561, 597, 606, 634, 635, 649, 738),
    ("7BF2GL1300", 463, 475, 502, 500, 533, 594, 629, 638, 667, 668, 681, 771),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 2 caceroleros LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 129,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo Fregadero 1 puerta extraíble BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7BF1PEB450", 143, 147, 156, 153, 164, 168, 177, 180, 187, 202, 210, 239),
    ("7BF1PEB500", 151, 155, 165, 162, 174, 177, 188, 190, 198, 211, 218, 249),
    ("7BF1PEB600", 166, 170, 182, 181, 195, 197, 210, 213, 223, 228, 235, 266),
    ("7BF1PEB700", 181, 185, 197, 196, 212, 214, 228, 232, 242, 248, 255, 289),
    ("7BF1PEB800", 196, 202, 214, 213, 231, 233, 248, 251, 263, 269, 277, 313),
    ("7BF1PEB900", 213, 218, 233, 232, 250, 253, 269, 273, 285, 292, 300, 339),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo Fregadero 1 puerta extraíble BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 129,
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
print(f"RESUMEN - PÁGINAS 125-129")
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
