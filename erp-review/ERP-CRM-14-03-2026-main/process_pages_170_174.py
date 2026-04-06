#!/usr/bin/env python3
"""
Process pages 170-174 from TARIFA-TECNICA-ZONACOCINAS
Pages 170-171: BAJOS 80cm DECORATIVOS
Pages 172-173: Title/Info pages (no products)
Page 174: SEMICOLUMNAS DE 130cm
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
# PAGE 170 - BAJOS 80cm DECORATIVOS
# ============================================

# Bajo botellero cuadros (3 estantes)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BBOT150", 269, 311, 270, 244, 282, 344, 383, 344, 370, 357, 362, 357),
    ("8BBOT300", 401, 461, 390, 347, 410, 492, 556, 492, 534, 514, 521, 514),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo botellero cuadros (3 estantes)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm DECORATIVOS",
        "sourcePage": 170, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo decorativo fondo 580mm (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BDEC150", 223, 264, 222, 195, 232, 293, 332, 293, 319, 311, 311, 311),
    ("8BDEC200", 230, 270, 229, 203, 239, 300, 338, 300, 326, 318, 318, 318),
    ("8BDEC300", 256, 297, 254, 223, 267, 343, 390, 343, 373, 364, 364, 364),
    ("8BDEC350", 268, 310, 266, 235, 279, 355, 401, 355, 385, 377, 377, 377),
    ("8BDEC400", 285, 334, 290, 254, 305, 385, 439, 385, 420, 411, 411, 411),
    ("8BDEC450", 341, 394, 331, 290, 348, 420, 477, 420, 458, 454, 454, 454),
    ("8BDEC500", 348, 401, 337, 297, 355, 447, 507, 447, 486, 461, 461, 461),
    ("8BDEC600", 355, 407, 344, 303, 361, 454, 515, 454, 494, 468, 468, 468),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo decorativo fondo 580mm (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm DECORATIVOS",
        "sourcePage": 170, "width": extract_width(ref), "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Bajo decorativo fondo 330mm (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BDECX150", 171, 196, 170, 151, 176, 210, 235, 210, 221, 221, 221, 221),
    ("8BDECX200", 174, 200, 173, 154, 181, 214, 239, 214, 224, 224, 224, 224),
    ("8BDECX300", 193, 223, 192, 171, 201, 246, 277, 246, 257, 257, 257, 257),
    ("8BDECX350", 207, 237, 206, 185, 215, 260, 291, 260, 272, 272, 272, 272),
    ("8BDECX400", 216, 251, 215, 191, 226, 281, 318, 281, 295, 295, 295, 295),
    ("8BDECX450", 229, 264, 226, 200, 237, 299, 338, 299, 313, 313, 313, 313),
    ("8BDECX500", 245, 279, 240, 214, 252, 316, 357, 316, 331, 331, 331, 331),
    ("8BDECX600", 267, 303, 266, 237, 278, 345, 390, 345, 360, 360, 360, 360),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo decorativo fondo 330mm (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm DECORATIVOS",
        "sourcePage": 170, "width": extract_width(ref), "height": 80, "depth": 33,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 171 - BAJOS 80cm DECORATIVOS
# ============================================

# Bajo terminal abierto (1 estante)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("8BTER300", 156, 169, 209, 167, 209, 211, 245, 211, 233, 192, 192, 192),
]:
    products_to_add.append({
        "reference": ref, "name": "Bajo terminal abierto (1 estante)",
        "programa": "ESTÁNDAR", "category": "BAJOS", "series": "BAJOS 80cm DECORATIVOS",
        "sourcePage": 171, "width": 30, "height": 80, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGES 172-173 - Title/Info pages (no products)
# ============================================

# ============================================
# PAGE 174 - SEMICOLUMNAS DE 130cm (ALTO 130cm FONDO 58cm)
# ============================================

# Semicolumna 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1P300", 159, 165, 177, 173, 188, 230, 248, 252, 267, 259, 267, 311),
    ("13SC1P350", 169, 174, 188, 187, 204, 234, 252, 256, 271, 271, 278, 322),
    ("13SC1P400", 179, 184, 198, 201, 221, 238, 256, 260, 274, 282, 289, 334),
    ("13SC1P450", 188, 193, 210, 214, 236, 255, 275, 280, 296, 294, 300, 344),
    ("13SC1P500", 197, 204, 222, 229, 252, 279, 302, 309, 327, 306, 312, 356),
    ("13SC1P600", 216, 224, 244, 256, 285, 288, 311, 317, 335, 330, 335, 379),
    ("13SC1P650", 249, 257, 280, 295, 327, 331, 357, 365, 385, 379, 385, 436),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 174, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC2P600", 255, 267, 292, 284, 313, 397, 433, 441, 469, 456, 469, 560),
    ("13SC2P700", 274, 287, 313, 311, 344, 405, 441, 449, 478, 480, 492, 583),
    ("13SC2P800", 293, 306, 335, 339, 378, 414, 449, 458, 486, 503, 516, 605),
    ("13SC2P900", 315, 327, 358, 369, 412, 450, 490, 500, 532, 528, 541, 629),
    ("13SC2P1000", 334, 348, 382, 396, 444, 499, 545, 557, 593, 551, 564, 651),
    ("13SC2P1200", 372, 385, 426, 452, 509, 516, 562, 573, 609, 597, 609, 696),
    ("13SC2P1300", 420, 435, 482, 510, 575, 583, 635, 648, 688, 675, 688, 787),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 2 puertas",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 174, "width": extract_width(ref), "height": 130, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Semicolumna 1 vitrina (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("13SC1V300", 225, 212, 224, 222, 235, 264, 281, 287, 300, 294, 300, 345),
    ("13SC1V350", 236, 228, 240, 240, 257, 274, 292, 296, 311, 311, 318, 362),
    ("13SC1V400", 248, 243, 257, 260, 279, 284, 301, 306, 320, 329, 335, 379),
    ("13SC1V450", 259, 257, 274, 279, 301, 307, 327, 332, 348, 345, 352, 396),
    ("13SC1V500", 271, 274, 291, 299, 323, 337, 360, 365, 384, 363, 370, 413),
    ("13SC1V600", 295, 305, 324, 338, 366, 357, 380, 385, 403, 398, 403, 447),
    ("13SC1V650", 333, 344, 367, 382, 414, 403, 430, 435, 456, 450, 456, 505),
]:
    products_to_add.append({
        "reference": ref, "name": "Semicolumna 1 vitrina (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "SEMICOLUMNAS", "series": "SEMICOLUMNAS DE 130cm",
        "sourcePage": 174, "width": extract_width(ref), "height": 130, "depth": 58,
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
    # Determine visualType based on category
    if "SEMICOLUMNAS" in product.get("category", ""):
        product["visualType"] = "semicolumna"
    else:
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
print(f"RESUMEN - PÁGINAS 170-174")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created_count}")
print(f"Productos actualizados: {updated_count}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {len(valid_references)}")
print(f"Total productos en BD: {db.products.count_documents({})}")
