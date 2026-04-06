#!/usr/bin/env python3
"""
Process pages 210-214 from TARIFA-TECNICA-ZONACOCINAS
PROGRAMA ESTÁNDAR - COLUMNAS - ALTO 200cm FONDO 58cm
Columnas con horno + microondas
"""

import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'kitchen_crm')]

# Load existing valid references
with open('/app/valid_references.json', 'r') as f:
    valid_references = json.load(f)

initial_count = len(valid_references)
print(f"Referencias válidas iniciales: {initial_count}")

products_to_add = []

# ============================================
# PAGE 210 - COLUMNAS 4 CAJONES + HORNO + MICRO
# ============================================

# Columna 4 cajones Bax + horno + micro + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CB1P600", 479, 480, 507, 482, 509, 534, 560, 566, 587, 625, 641, 663),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno + micro + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 210, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno + micro + 1 puerta (Derecha/Izquierda)
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CL1P600", 584, 585, 612, 586, 614, 638, 665, 671, 691, 730, 746, 767),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno + micro + 1 puerta (Derecha/Izquierda)",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 210, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Bax + horno + micro + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CB1PABL600", 605, 606, 633, 608, 635, 660, 686, 692, 713, 751, 767, 789),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno + micro + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 210, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno + micro + 1 puerta abatible HK
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CL1PABL600", 710, 711, 738, 712, 740, 764, 791, 797, 817, 856, 872, 893),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno + micro + 1 puerta abatible HK",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 210, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 211 - COLUMNAS 4 CAJONES + HORNO + MICRO + 2 PUERTAS / CACEROLEROS
# ============================================

# Columna 4 cajones Bax + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CB2P600", 504, 506, 536, 507, 537, 588, 620, 627, 652, 693, 717, 768),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Bax + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 211, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 4 cajones Lux + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM4CL2P600", 609, 611, 639, 611, 642, 693, 725, 732, 756, 798, 822, 872),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 4 cajones Lux + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 211, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CB1P600", 429, 438, 462, 452, 480, 495, 519, 525, 545, 597, 616, 672),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 211, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CL1P600", 511, 519, 543, 532, 561, 575, 600, 606, 626, 678, 698, 753),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 211, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 212 - COLUMNAS 1 CACEROLERO + 2 CAJONES + HORNO + MICRO
# ============================================

# Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CB1PABL600", 555, 564, 588, 578, 606, 621, 645, 651, 671, 723, 742, 798),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 212, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CL1PABL600", 637, 645, 669, 658, 687, 701, 726, 732, 752, 804, 824, 879),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 212, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Bax + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CB2P600", 455, 463, 489, 477, 507, 548, 579, 586, 610, 666, 693, 777),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Bax + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 212, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 1 cacerolero + 2 cajones Lux + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM1G2CL2P600", 536, 544, 571, 558, 588, 629, 659, 667, 691, 747, 774, 858),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 1 cacerolero + 2 cajones Lux + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 212, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 213 - COLUMNAS 2 CACEROLEROS + 1 CAJÓN + HORNO + MICRO
# ============================================

# Columna 2 caceroleros + 1 cajón Bax + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CB1P600", 451, 460, 485, 474, 504, 519, 545, 551, 572, 627, 647, 706),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Bax + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 213, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajón Lux + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CL1P600", 537, 545, 570, 559, 589, 604, 630, 636, 657, 712, 733, 790),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Lux + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 213, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajón Bax + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CB1PABL600", 577, 586, 611, 600, 630, 645, 671, 677, 698, 753, 773, 832),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Bax + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 213, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajón Lux + horno + micro + 1 puerta abatible
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CL1PABL600", 663, 671, 696, 685, 715, 730, 756, 762, 783, 838, 859, 916),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Lux + horno + micro + 1 puerta abatible",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 213, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PAGE 214 - COLUMNAS 2 CACEROLEROS + HORNO + MICRO
# ============================================

# Columna 2 caceroleros + 1 cajón Bax + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CB2P600", 480, 488, 515, 502, 532, 573, 604, 611, 635, 691, 718, 802),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Bax + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 214, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros + 1 cajón Lux + horno + micro + 2 puertas
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2G1CL2P600", 562, 570, 597, 584, 614, 655, 686, 693, 717, 773, 800, 884),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros + 1 cajón Lux + horno + micro + 2 puertas",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 214, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Bax + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GB1P600", 380, 395, 417, 421, 449, 455, 478, 484, 503, 570, 593, 680),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Bax + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 214, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# Columna 2 caceroleros Lux + horno + micro + 1 puerta
for ref, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12 in [
    ("20HM2GL1P600", 438, 452, 474, 478, 507, 511, 536, 541, 560, 628, 650, 738),
]:
    products_to_add.append({
        "reference": ref, "name": "Columna 2 caceroleros Lux + horno + micro + 1 puerta",
        "programa": "ESTÁNDAR", "category": "COLUMNAS", "series": "COLUMNAS DE 200cm FONDO 58cm",
        "sourcePage": 214, "width": 60, "height": 200, "depth": 58,
        "zonePoints": {"Z1": z1, "Z2": z2, "Z3": z3, "Z4": z4, "Z5": z5, "Z6": z6, "Z7": z7, "Z8": z8, "Z9": z9, "Z10": z10, "Z11": z11, "Z12": z12}
    })

# ============================================
# PROCESS ALL PRODUCTS
# ============================================

created = 0
updated = 0
new_refs = []

for product in products_to_add:
    ref = product["reference"]
    
    # Add to valid references if not already present
    if ref not in valid_references:
        valid_references.append(ref)
        new_refs.append(ref)
    
    # Check if product exists
    existing = db.products.find_one({"reference": ref})
    
    if existing:
        # Update existing product
        db.products.update_one(
            {"reference": ref},
            {"$set": product}
        )
        updated += 1
    else:
        # Insert new product
        db.products.insert_one(product)
        created += 1

# Save updated valid references
with open('/app/valid_references.json', 'w') as f:
    json.dump(sorted(valid_references), f, indent=2)

# Final summary
final_count = len(valid_references)
total_products = db.products.count_documents({})

print(f"\n{'='*50}")
print(f"RESUMEN - PÁGINAS 210-214")
print(f"{'='*50}")
print(f"Productos procesados: {len(products_to_add)}")
print(f"Productos creados: {created}")
print(f"Productos actualizados: {updated}")
print(f"Nuevas referencias: {len(new_refs)}")
print(f"Referencias válidas: {initial_count} → {final_count}")
print(f"Total productos en BD: {total_products}")
