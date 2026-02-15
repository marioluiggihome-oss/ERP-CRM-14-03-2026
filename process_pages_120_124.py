#!/usr/bin/env python3
"""
Process pages 121-124 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS - BAJOS 70cm FONDO ESTÁNDAR
Page 120 is informational (drawer systems) - no products
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
# PAGE 121 - PROGRAMA ESTÁNDAR - BAJOS DE 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1P300", 95, 98, 104, 99, 107, 119, 127, 128, 134, 149, 158, 188),
    ("7B1P350", 100, 103, 111, 106, 114, 123, 131, 133, 140, 156, 164, 194),
    ("7B1P400", 106, 109, 118, 113, 123, 129, 138, 140, 146, 164, 171, 202),
    ("7B1P450", 112, 116, 125, 122, 132, 137, 146, 148, 155, 171, 179, 208),
    ("7B1P500", 118, 122, 132, 129, 142, 145, 155, 158, 166, 179, 186, 215),
    ("7B1P600", 130, 134, 146, 145, 160, 162, 174, 177, 187, 192, 200, 230),
    ("7B1P650", 130, 134, 146, 145, 160, 162, 174, 177, 187, 192, 200, 230),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 121,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2P600", 155, 162, 176, 166, 181, 205, 221, 225, 237, 266, 281, 342),
    ("7B2P700", 168, 174, 190, 181, 197, 214, 231, 235, 248, 280, 296, 357),
    ("7B2P800", 180, 186, 203, 194, 214, 226, 243, 247, 260, 295, 311, 371),
    ("7B2P900", 193, 201, 219, 213, 235, 244, 263, 267, 281, 311, 327, 386),
    ("7B2P1000", 206, 214, 235, 228, 253, 259, 280, 285, 301, 326, 341, 401),
    ("7B2P1200", 230, 238, 263, 259, 289, 294, 318, 324, 343, 355, 370, 429),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 121,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1V300", 152, 134, 144, 138, 147, 151, 160, 163, 170, 188, 196, 233),
    ("7B1V350", 162, 145, 155, 150, 160, 160, 170, 171, 181, 200, 209, 246),
    ("7B1V400", 171, 155, 166, 162, 172, 170, 181, 183, 190, 212, 221, 257),
    ("7B1V450", 181, 166, 177, 174, 188, 183, 194, 196, 206, 223, 232, 269),
    ("7B1V500", 189, 190, 190, 187, 202, 195, 208, 210, 221, 235, 245, 279),
    ("7B1V600", 207, 200, 213, 212, 229, 223, 237, 240, 252, 259, 269, 303),
    ("7B1V650", 234, 227, 240, 239, 256, 250, 265, 268, 279, 287, 296, 331),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 vitrina",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 121,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 vitrinas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2V600", 277, 242, 258, 247, 266, 273, 294, 297, 313, 347, 366, 439),
    ("7B2V700", 296, 264, 282, 271, 292, 292, 311, 316, 332, 371, 390, 462),
    ("7B2V800", 314, 284, 303, 295, 319, 311, 332, 420, 353, 395, 414, 486),
    ("7B2V900", 332, 305, 328, 320, 347, 420, 359, 365, 383, 418, 437, 509),
    ("7B2V1000", 351, 328, 352, 345, 374, 363, 386, 393, 412, 442, 461, 531),
    ("7B2V1200", 384, 370, 398, 396, 431, 417, 446, 454, 477, 490, 508, 579),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 vitrinas",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 121,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 122 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 1 puerta 560mm + 1 cajón 140mm BAX (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1P1CB300", 134, 137, 145, 141, 150, 173, 185, 188, 196, 215, 226, 254),
    ("7B1P1CB350", 142, 145, 154, 146, 156, 179, 190, 193, 203, 224, 234, 264),
    ("7B1P1CB400", 149, 152, 163, 155, 167, 184, 195, 198, 208, 224, 252, 280),
    ("7B1P1CB450", 156, 160, 171, 164, 176, 191, 204, 207, 216, 242, 252, 280),
    ("7B1P1CB500", 164, 168, 181, 172, 187, 197, 210, 213, 224, 251, 260, 289),
    ("7B1P1CB600", 179, 184, 198, 190, 207, 212, 227, 230, 242, 269, 278, 307),
    ("7B1P1CB650", 211, 217, 234, 225, 245, 251, 268, 272, 286, 317, 329, 362),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta 560mm + 1 cajón 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 122,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta 560mm + 1 cajón 140mm LUX (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1P1CL300", 170, 172, 181, 175, 186, 209, 221, 223, 232, 250, 260, 290),
    ("7B1P1CL350", 177, 180, 190, 182, 192, 214, 226, 229, 238, 259, 270, 298),
    ("7B1P1CL400", 185, 188, 198, 191, 203, 219, 231, 234, 244, 268, 278, 308),
    ("7B1P1CL450", 192, 195, 207, 200, 212, 227, 239, 243, 252, 277, 288, 316),
    ("7B1P1CL500", 200, 204, 216, 208, 223, 233, 246, 249, 259, 286, 296, 324),
    ("7B1P1CL600", 214, 219, 234, 226, 243, 248, 263, 266, 277, 305, 314, 342),
    ("7B1P1CL650", 253, 259, 276, 267, 287, 292, 310, 314, 328, 359, 371, 404),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta 560mm + 1 cajón 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 122,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 560mm + 1 cajón 140 BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2P1CB600", 204, 210, 227, 214, 232, 267, 286, 291, 307, 341, 360, 420),
    ("7B2P1CB700", 219, 228, 248, 232, 253, 290, 311, 317, 335, 377, 408, 456),
    ("7B2P1CB800", 235, 244, 266, 250, 273, 308, 331, 337, 356, 401, 425, 479),
    ("7B2P1CB900", 252, 261, 285, 269, 295, 324, 349, 355, 375, 425, 445, 502),
    ("7B2P1CB1000", 269, 278, 303, 287, 315, 337, 362, 369, 390, 443, 463, 520),
    ("7B2P1CB1200", 298, 309, 339, 322, 356, 366, 395, 402, 424, 479, 499, 554),
    ("7B2P1CB1300", 352, 364, 400, 381, 420, 433, 466, 475, 501, 565, 589, 654),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas 560mm + 1 cajón 140 BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 122,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 560mm + 1 cajón 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2P1CL600", 239, 246, 204, 210, 227, 214, 232, 267, 286, 291, 307, 341),
    ("7B2P1CL700", 255, 264, 284, 268, 289, 324, 347, 353, 371, 413, 444, 491),
    ("7B2P1CL800", 271, 279, 301, 286, 309, 343, 366, 373, 392, 437, 461, 515),
    ("7B2P1CL900", 288, 297, 320, 306, 331, 360, 385, 391, 411, 461, 481, 538),
    ("7B2P1CL1000", 305, 314, 339, 322, 352, 373, 398, 404, 425, 479, 499, 555),
    ("7B2P1CL1200", 334, 345, 375, 358, 392, 403, 431, 438, 460, 516, 534, 591),
    ("7B2P1CL1300", 394, 407, 442, 422, 462, 476, 508, 517, 543, 608, 631, 697),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas 560mm + 1 cajón 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 122,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 123 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 4 cajones 175mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B4CB300", 229, 222, 230, 227, 236, 265, 276, 280, 289, 301, 311, 307),
    ("7B4CB350", 237, 231, 242, 235, 245, 269, 281, 285, 294, 311, 319, 314),
    ("7B4CB400", 247, 242, 251, 243, 255, 274, 287, 290, 299, 327, 335, 331),
    ("7B4CB450", 255, 250, 261, 251, 263, 288, 301, 306, 315, 327, 335, 331),
    ("7B4CB500", 265, 260, 273, 259, 272, 294, 307, 310, 420, 344, 339, 339),
    ("7B4CB600", 282, 278, 294, 275, 290, 303, 317, 319, 331, 352, 360, 356),
    ("7B4CB700", 307, 306, 326, 312, 333, 356, 377, 381, 397, 429, 481, 435),
    ("7B4CB800", 329, 324, 345, 329, 352, 392, 416, 422, 441, 467, 497, 473),
    ("7B4CB900", 348, 345, 369, 345, 371, 421, 448, 455, 476, 499, 515, 506),
    ("7B4CB1000", 374, 364, 391, 363, 389, 431, 458, 464, 486, 516, 532, 522),
    ("7B4CB1200", 410, 402, 432, 396, 424, 450, 478, 484, 506, 550, 565, 555),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 4 cajones 175mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 123,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 4 cajones 175mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B4CL300", 370, 361, 372, 368, 379, 412, 425, 429, 440, 455, 465, 460),
    ("7B4CL350", 380, 373, 384, 377, 389, 417, 432, 435, 446, 465, 475, 469),
    ("7B4CL400", 391, 384, 397, 386, 400, 423, 437, 441, 452, 475, 484, 479),
    ("7B4CL450", 401, 395, 408, 396, 411, 439, 455, 459, 471, 485, 495, 488),
    ("7B4CL500", 413, 406, 421, 405, 421, 445, 461, 465, 477, 495, 504, 499),
    ("7B4CL600", 434, 428, 446, 425, 442, 457, 473, 477, 489, 515, 524, 518),
    ("7B4CL700", 461, 460, 483, 467, 492, 519, 543, 548, 567, 605, 664, 610),
    ("7B4CL800", 488, 482, 507, 487, 513, 561, 589, 595, 618, 649, 683, 654),
    ("7B4CL900", 509, 506, 533, 508, 537, 594, 626, 633, 658, 686, 705, 693),
    ("7B4CL1000", 541, 529, 559, 527, 558, 607, 638, 646, 670, 706, 725, 713),
    ("7B4CL1200", 583, 573, 608, 566, 600, 630, 662, 669, 694, 746, 763, 752),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 4 cajones 175mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 123,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 5 cajones 140mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B5CB300", 274, 267, 275, 272, 281, 310, 321, 326, 334, 347, 356, 352),
    ("7B5CB350", 282, 276, 287, 280, 290, 314, 327, 330, 339, 356, 364, 359),
    ("7B5CB400", 292, 287, 296, 288, 300, 319, 332, 335, 344, 364, 372, 368),
    ("7B5CB450", 300, 295, 307, 296, 308, 333, 347, 351, 360, 372, 380, 376),
    ("7B5CB500", 310, 306, 318, 305, 317, 339, 352, 355, 365, 381, 390, 384),
    ("7B5CB600", 328, 323, 339, 320, 335, 349, 362, 364, 376, 397, 405, 401),
    ("7B5CB700", 352, 351, 371, 357, 378, 401, 422, 426, 442, 475, 526, 480),
    ("7B5CB800", 374, 370, 391, 374, 397, 437, 461, 467, 486, 512, 542, 518),
    ("7B5CB900", 393, 391, 414, 391, 416, 466, 494, 500, 521, 544, 560, 551),
    ("7B5CB1000", 419, 410, 436, 408, 434, 476, 503, 509, 531, 561, 578, 567),
    ("7B5CB1200", 455, 447, 477, 441, 469, 496, 523, 529, 551, 595, 610, 601),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 5 cajones 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 123,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 124 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO ESTÁNDAR
# ============================================

# Bajo 5 cajones 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B5CL300", 449, 440, 452, 446, 461, 502, 520, 524, 538, 557, 569, 563),
    ("7B5CL350", 462, 454, 467, 458, 474, 508, 526, 530, 544, 568, 581, 573),
    ("7B5CL400", 475, 466, 482, 469, 486, 516, 532, 537, 551, 580, 591, 585),
    ("7B5CL450", 487, 479, 497, 480, 498, 534, 554, 559, 574, 591, 603, 596),
    ("7B5CL500", 500, 492, 511, 491, 510, 541, 561, 566, 581, 603, 614, 608),
    ("7B5CL600", 525, 519, 541, 515, 536, 554, 574, 579, 594, 626, 638, 630),
    ("7B5CL700", 558, 557, 585, 566, 596, 630, 659, 667, 690, 738, 811, 744),
    ("7B5CL800", 590, 583, 614, 589, 622, 681, 716, 725, 753, 791, 834, 798),
    ("7B5CL900", 615, 611, 645, 613, 648, 721, 761, 770, 801, 835, 859, 845),
    ("7B5CL1000", 652, 638, 675, 636, 673, 840, 774, 783, 815, 859, 882, 868),
    ("7B5CL1200", 702, 690, 734, 681, 723, 761, 801, 811, 841, 905, 928, 914),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 5 cajones 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 124,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 280mm + 3 cajones 140mm BAX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G3CB300", 243, 238, 249, 250, 265, 300, 317, 320, 334, 364, 379, 401),
    ("7B1G3CB350", 253, 250, 263, 260, 276, 308, 324, 329, 342, 380, 395, 419),
    ("7B1G3CB400", 264, 261, 275, 272, 289, 313, 331, 335, 348, 389, 403, 427),
    ("7B1G3CB450", 275, 272, 288, 282, 301, 329, 348, 352, 366, 404, 419, 445),
    ("7B1G3CB500", 286, 285, 301, 294, 314, 335, 353, 357, 372, 413, 427, 454),
    ("7B1G3CB600", 307, 308, 327, 315, 337, 347, 364, 369, 383, 431, 445, 471),
    ("7B1G3CB700", 333, 337, 361, 352, 380, 403, 428, 435, 455, 540, 592, 597),
    ("7B1G3CB800", 359, 360, 386, 375, 406, 449, 481, 488, 513, 574, 609, 634),
    ("7B1G3CB900", 381, 384, 414, 400, 434, 491, 527, 536, 564, 606, 629, 667),
    ("7B1G3CB1000", 415, 413, 446, 433, 471, 523, 561, 570, 601, 670, 699, 752),
    ("7B1G3CB1200", 459, 459, 498, 476, 519, 565, 607, 616, 649, 706, 840, 786),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm BAX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 124,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G3CL300", 387, 382, 394, 395, 410, 444, 461, 465, 479, 509, 524, 546),
    ("7B1G3CL350", 398, 395, 406, 405, 421, 453, 469, 474, 487, 524, 540, 563),
    ("7B1G3CL400", 408, 405, 420, 417, 434, 458, 475, 479, 492, 533, 548, 572),
    ("7B1G3CL450", 419, 417, 433, 427, 446, 474, 491, 497, 511, 548, 564, 590),
    ("7B1G3CL500", 431, 429, 446, 439, 459, 479, 498, 502, 517, 558, 572, 599),
    ("7B1G3CL600", 453, 453, 471, 460, 482, 491, 509, 515, 528, 575, 590, 616),
    ("7B1G3CL700", 478, 482, 506, 497, 525, 548, 573, 580, 600, 685, 737, 743),
    ("7B1G3CL800", 504, 505, 531, 521, 551, 595, 626, 633, 658, 719, 755, 779),
    ("7B1G3CL900", 527, 530, 560, 545, 579, 637, 672, 681, 709, 751, 774, 812),
    ("7B1G3CL1000", 561, 559, 591, 579, 616, 668, 707, 716, 747, 815, 845, 898),
    ("7B1G3CL1200", 604, 605, 644, 621, 665, 711, 752, 762, 795, 851, 881, 932),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO ESTÁNDAR",
        "sourcePage": 124,
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
print(f"RESUMEN - PÁGINAS 120-124")
print(f"(Página 120 es informativa - sistemas de apertura)")
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
