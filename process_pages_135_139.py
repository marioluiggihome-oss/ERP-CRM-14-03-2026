#!/usr/bin/env python3
"""
Process pages 135-139 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - BAJOS - BAJOS 70cm FONDO 33cm
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
# PAGE 135 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 2 puertas fondo 330
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2PX600", 141, 147, 162, 151, 166, 190, 206, 210, 222, 251, 267, 328),
    ("7B2PX700", 152, 159, 174, 165, 182, 199, 216, 220, 233, 265, 280, 341),
    ("7B2PX800", 164, 170, 187, 179, 198, 210, 227, 232, 245, 278, 294, 355),
    ("7B2PX900", 176, 184, 203, 195, 217, 226, 245, 249, 265, 294, 310, 370),
    ("7B2PX1000", 188, 196, 216, 210, 234, 242, 261, 267, 282, 308, 323, 383),
    ("7B2PX1200", 210, 218, 243, 239, 269, 278, 299, 305, 323, 335, 350, 410),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas fondo 330",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 135,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 vitrina fondo 330 (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1VX300", 127, 112, 120, 114, 123, 126, 133, 135, 142, 156, 164, 194),
    ("7B1VX350", 134, 121, 129, 125, 133, 133, 142, 143, 150, 166, 174, 205),
    ("7B1VX400", 143, 129, 139, 134, 144, 142, 150, 152, 159, 176, 184, 214),
    ("7B1VX450", 150, 139, 148, 145, 156, 152, 162, 164, 171, 186, 193, 224),
    ("7B1VX500", 158, 148, 159, 155, 168, 163, 173, 175, 184, 196, 204, 233),
    ("7B1VX600", 172, 166, 177, 176, 191, 186, 197, 201, 210, 216, 224, 253),
    ("7B1VX650", 186, 180, 192, 190, 207, 201, 213, 216, 227, 233, 242, 273),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 vitrina fondo 330",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 135,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 vitrinas fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2VX600", 231, 202, 215, 206, 222, 228, 245, 248, 260, 289, 306, 365),
    ("7B2VX700", 247, 219, 235, 226, 244, 244, 259, 264, 276, 309, 324, 385),
    ("7B2VX800", 261, 236, 253, 246, 266, 259, 276, 280, 294, 329, 344, 405),
    ("7B2VX900", 276, 254, 273, 267, 289, 280, 299, 305, 319, 349, 364, 424),
    ("7B2VX1000", 292, 273, 293, 288, 312, 302, 322, 328, 343, 369, 384, 443),
    ("7B2VX1200", 320, 308, 332, 330, 359, 348, 372, 377, 397, 408, 423, 482),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 vitrinas fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 135,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 puerta + 1 cajón BAX fondo 330mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1P1CBX300", 122, 124, 132, 128, 138, 161, 172, 175, 184, 203, 213, 242),
    ("7B1P1CBX350", 129, 131, 141, 133, 144, 165, 176, 181, 189, 211, 222, 250),
    ("7B1P1CBX400", 135, 139, 149, 142, 153, 170, 183, 185, 194, 219, 230, 258),
    ("7B1P1CBX450", 143, 146, 158, 150, 163, 177, 190, 193, 203, 228, 238, 267),
    ("7B1P1CBX500", 150, 154, 167, 159, 173, 184, 196, 200, 210, 236, 247, 275),
    ("7B1P1CBX600", 164, 169, 184, 175, 192, 197, 212, 215, 227, 254, 264, 292),
    ("7B1P1CBX650", 185, 190, 207, 198, 216, 222, 239, 242, 255, 286, 296, 328),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta + 1 cajón BAX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 135,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 136 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 1 puerta + 1 cajón LUX fondo 330mm (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1P1CLX300", 156, 159, 167, 162, 171, 195, 207, 209, 218, 236, 247, 276),
    ("7B1P1CLX350", 163, 165, 175, 167, 177, 200, 211, 214, 224, 245, 255, 285),
    ("7B1P1CLX400", 169, 172, 183, 175, 187, 204, 216, 219, 228, 253, 264, 292),
    ("7B1P1CLX450", 176, 180, 191, 184, 196, 211, 224, 227, 236, 261, 271, 300),
    ("7B1P1CLX500", 183, 187, 201, 192, 206, 216, 230, 233, 243, 270, 279, 309),
    ("7B1P1CLX600", 196, 202, 216, 208, 225, 230, 245, 248, 258, 287, 296, 324),
    ("7B1P1CLX650", 220, 226, 242, 233, 252, 258, 274, 278, 289, 321, 332, 363),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 puerta + 1 cajón LUX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 136,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 560mm + 1 cajón 140mm BAX fondo 300mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2P1CBX600", 189, 195, 212, 200, 217, 252, 271, 276, 292, 327, 345, 404),
    ("7B2P1CBX700", 204, 213, 232, 216, 237, 273, 295, 301, 319, 362, 393, 440),
    ("7B2P1CBX800", 219, 228, 249, 233, 257, 291, 315, 320, 339, 385, 410, 462),
    ("7B2P1CBX900", 234, 244, 268, 252, 278, 307, 332, 338, 358, 407, 427, 485),
    ("7B2P1CBX1000", 251, 259, 286, 269, 297, 319, 344, 351, 371, 425, 445, 502),
    ("7B2P1CBX1200", 278, 290, 319, 302, 420, 347, 375, 382, 404, 459, 479, 536),
    ("7B2P1CBX1300", 314, 327, 361, 342, 380, 392, 424, 432, 457, 519, 541, 605),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas 560mm + 1 cajón 140mm BAX fondo 300mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 136,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 2 puertas 560mm + 1 cajón 140mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B2P1CLX600", 221, 228, 245, 231, 250, 284, 303, 309, 323, 359, 378, 437),
    ("7B2P1CLX700", 236, 245, 265, 249, 269, 306, 328, 334, 351, 394, 424, 471),
    ("7B2P1CLX800", 251, 259, 280, 265, 288, 322, 347, 352, 371, 416, 441, 494),
    ("7B2P1CLX900", 266, 275, 298, 282, 309, 338, 362, 369, 389, 438, 459, 516),
    ("7B2P1CLX1000", 281, 290, 316, 299, 328, 349, 375, 381, 401, 455, 476, 532),
    ("7B2P1CLX1200", 308, 318, 349, 331, 364, 376, 404, 411, 434, 488, 508, 564),
    ("7B2P1CLX1300", 348, 360, 394, 374, 412, 425, 457, 464, 490, 552, 574, 637),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 2 puertas 560mm + 1 cajón 140mm LUX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 136,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 137 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 4 cajones 175mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B4CBX300", 219, 211, 222, 217, 229, 261, 275, 279, 290, 305, 315, 310),
    ("7B4CBX350", 230, 223, 234, 226, 238, 267, 280, 285, 295, 314, 324, 319),
    ("7B4CBX400", 239, 233, 246, 235, 249, 272, 286, 290, 300, 323, 333, 328),
    ("7B4CBX450", 250, 244, 257, 245, 258, 288, 303, 308, 319, 333, 342, 337),
    ("7B4CBX500", 260, 254, 270, 254, 269, 293, 309, 313, 324, 342, 352, 347),
    ("7B4CBX600", 280, 275, 293, 272, 289, 305, 320, 323, 335, 361, 371, 364),
    ("7B4CBX700", 307, 307, 329, 313, 338, 365, 389, 394, 413, 452, 509, 456),
    ("7B4CBX800", 333, 328, 352, 332, 358, 405, 434, 441, 463, 494, 528, 499),
    ("7B4CBX900", 353, 350, 377, 352, 380, 438, 469, 478, 502, 529, 548, 538),
    ("7B4CBX1000", 383, 372, 402, 370, 400, 449, 481, 488, 513, 548, 567, 555),
    ("7B4CBX1200", 423, 414, 448, 406, 440, 470, 504, 512, 538, 586, 604, 592),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 4 cajones 175mm BAX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 137,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 4 cajones 175mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B4CLX300", 353, 344, 354, 350, 361, 394, 408, 412, 422, 438, 447, 442),
    ("7B4CLX350", 361, 354, 365, 358, 370, 398, 413, 416, 426, 445, 456, 450),
    ("7B4CLX400", 371, 363, 376, 365, 379, 402, 417, 420, 431, 454, 464, 458),
    ("7B4CLX450", 379, 373, 386, 374, 387, 417, 433, 437, 448, 462, 471, 466),
    ("7B4CLX500", 389, 382, 398, 381, 397, 421, 437, 441, 453, 470, 480, 475),
    ("7B4CLX600", 406, 401, 419, 398, 415, 429, 445, 449, 461, 487, 497, 490),
    ("7B4CLX700", 429, 429, 452, 437, 461, 488, 511, 518, 536, 574, 632, 580),
    ("7B4CLX800", 454, 448, 473, 453, 479, 527, 554, 562, 584, 614, 649, 621),
    ("7B4CLX900", 471, 468, 496, 470, 499, 557, 588, 596, 621, 648, 667, 655),
    ("7B4CLX1000", 500, 488, 518, 486, 517, 566, 597, 605, 629, 665, 684, 672),
    ("7B4CLX1200", 536, 525, 560, 518, 552, 582, 614, 621, 646, 697, 716, 704),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 4 cajones 175mm LUX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 137,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 138 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 5 cajones 200mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B5CBX300", 266, 255, 268, 263, 276, 317, 335, 339, 353, 372, 384, 378),
    ("7B5CBX350", 277, 268, 282, 273, 288, 323, 341, 345, 359, 382, 395, 389),
    ("7B5CBX400", 289, 280, 296, 284, 300, 330, 347, 352, 365, 394, 406, 399),
    ("7B5CBX450", 301, 293, 311, 294, 312, 349, 369, 373, 389, 405, 417, 411),
    ("7B5CBX500", 313, 307, 324, 306, 324, 355, 375, 379, 395, 417, 428, 421),
    ("7B5CBX600", 337, 331, 353, 327, 348, 366, 386, 391, 406, 439, 450, 443),
    ("7B5CBX700", 369, 369, 396, 377, 407, 442, 471, 478, 502, 549, 623, 555),
    ("7B5CBX800", 400, 393, 424, 399, 433, 491, 527, 536, 563, 602, 644, 608),
    ("7B5CBX900", 424, 420, 455, 422, 458, 530, 570, 580, 610, 644, 668, 654),
    ("7B5CBX1000", 460, 446, 484, 444, 482, 543, 582, 591, 623, 667, 690, 676),
    ("7B5CBX1200", 508, 496, 540, 487, 529, 567, 607, 615, 647, 711, 734, 719),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 5 cajones 200mm BAX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 138,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 5 cajones 200mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B5CLX300", 440, 421, 433, 427, 442, 483, 501, 505, 519, 538, 550, 544),
    ("7B5CLX350", 453, 433, 446, 437, 453, 487, 505, 509, 524, 547, 560, 553),
    ("7B5CLX400", 465, 443, 459, 446, 463, 492, 510, 515, 528, 557, 569, 562),
    ("7B5CLX450", 478, 455, 471, 456, 474, 510, 529, 534, 550, 567, 579, 571),
    ("7B5CLX500", 491, 466, 485, 465, 484, 515, 534, 539, 554, 576, 588, 581),
    ("7B5CLX600", 517, 488, 510, 484, 505, 524, 544, 548, 564, 595, 607, 600),
    ("7B5CLX700", 549, 522, 550, 531, 562, 595, 625, 632, 655, 704, 776, 710),
    ("7B5CLX800", 583, 544, 575, 550, 584, 643, 678, 687, 714, 752, 795, 759),
    ("7B5CLX900", 607, 568, 603, 570, 606, 678, 718, 728, 758, 792, 816, 802),
    ("7B5CLX1000", 645, 589, 629, 589, 627, 688, 728, 737, 768, 812, 835, 821),
    ("7B5CLX1200", 696, 635, 678, 626, 669, 707, 746, 755, 786, 851, 874, 859),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 5 cajones 200mm LUX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 138,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 139 - PROGRAMA ESTÁNDAR - BAJOS 70cm FONDO 33cm
# ============================================

# Bajo 1 cacerolero 280mm + 3 cajones 140mm BAX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G3CBX300", 234, 230, 240, 242, 256, 292, 309, 312, 326, 356, 371, 393),
    ("7B1G3CBX350", 245, 240, 253, 252, 268, 300, 316, 320, 333, 371, 385, 410),
    ("7B1G3CBX400", 255, 252, 266, 263, 279, 305, 321, 326, 339, 379, 394, 418),
    ("7B1G3CBX450", 266, 263, 278, 274, 292, 319, 338, 342, 357, 395, 410, 436),
    ("7B1G3CBX500", 276, 274, 291, 285, 303, 324, 343, 348, 362, 403, 418, 444),
    ("7B1G3CBX600", 296, 296, 316, 305, 327, 420, 354, 358, 373, 420, 435, 461),
    ("7B1G3CBX700", 321, 326, 350, 340, 369, 392, 417, 423, 443, 528, 581, 587),
    ("7B1G3CBX800", 348, 348, 375, 363, 394, 438, 469, 477, 501, 563, 597, 622),
    ("7B1G3CBX900", 369, 372, 401, 386, 420, 479, 515, 523, 551, 592, 616, 653),
    ("7B1G3CBX1000", 401, 399, 433, 419, 458, 508, 547, 557, 587, 656, 686, 738),
    ("7B1G3CBX1200", 443, 443, 482, 460, 503, 549, 591, 601, 633, 690, 719, 772),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm BAX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 139,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX fondo 330mm
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("7B1G3CLX300", 370, 365, 376, 378, 392, 427, 444, 448, 461, 492, 506, 528),
    ("7B1G3CLX350", 379, 376, 387, 386, 402, 434, 450, 455, 468, 505, 521, 544),
    ("7B1G3CLX400", 389, 385, 399, 396, 413, 438, 455, 459, 473, 512, 527, 551),
    ("7B1G3CLX450", 398, 395, 411, 405, 424, 452, 469, 475, 489, 526, 542, 568),
    ("7B1G3CLX500", 406, 405, 422, 416, 435, 456, 475, 479, 494, 533, 549, 575),
    ("7B1G3CLX600", 425, 425, 444, 434, 456, 464, 483, 487, 502, 548, 564, 589),
    ("7B1G3CLX700", 448, 453, 476, 467, 495, 518, 543, 549, 569, 654, 707, 713),
    ("7B1G3CLX800", 471, 471, 499, 487, 518, 561, 593, 601, 625, 687, 721, 746),
    ("7B1G3CLX900", 489, 494, 523, 508, 542, 600, 635, 644, 672, 714, 737, 775),
    ("7B1G3CLX1000", 521, 518, 551, 538, 576, 628, 667, 675, 706, 775, 805, 857),
    ("7B1G3CLX1200", 558, 558, 596, 574, 617, 663, 704, 715, 748, 804, 834, 885),
]:
    products_to_add.append({
        "reference": ref,
        "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX fondo 330mm",
        "programa": "ESTÁNDAR",
        "category": "BAJOS",
        "series": "BAJOS 70cm FONDO 33cm",
        "sourcePage": 139,
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
print(f"RESUMEN - PÁGINAS 135-139")
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
