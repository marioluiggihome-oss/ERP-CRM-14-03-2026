#!/usr/bin/env python3
"""
Script para procesar páginas 235-239 del catálogo TARIFA-COMPLETA.pdf
PROGRAMA ESTANDAR - COLUMNAS - ALTO 220cm FONDO 58cm
Columnas con horno + micro
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'kitchen_budget')

# Productos de las páginas 235-239
PRODUCTS_PAGES_235_239 = [
    # ========== PÁGINA 235 ==========
    # Columna 2 puertas + horno + micro + 2 puertas
    {
        "reference": "22HM1P1PABL600",
        "name": "Columna 2 puertas + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1P1PABL600",
        "points": 401,
        "zonePoints": {"Z1": 401, "Z2": 412, "Z3": 433, "Z4": 428, "Z5": 454, "Z6": 466, "Z7": 488, "Z8": 494, "Z9": 510, "Z10": 521, "Z11": 537, "Z12": 596},
        "page": 235
    },
    # Columna 4 cajones Bax + horno + micro + 1 puerta (Derecha/Izquierda)
    {
        "reference": "22HM4CB1P600",
        "name": "Columna 4 cajones Bax + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM4CB1P600",
        "points": 499,
        "zonePoints": {"Z1": 499, "Z2": 498, "Z3": 527, "Z4": 505, "Z5": 537, "Z6": 554, "Z7": 582, "Z8": 589, "Z9": 611, "Z10": 643, "Z11": 658, "Z12": 683},
        "page": 235
    },
    # Columna 4 cajones Lux + horno + micro + 1 puerta (Derecha/Izquierda)
    {
        "reference": "22HM4CL1P600",
        "name": "Columna 4 cajones Lux + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM4CL1P600",
        "points": 603,
        "zonePoints": {"Z1": 603, "Z2": 603, "Z3": 632, "Z4": 610, "Z5": 642, "Z6": 659, "Z7": 687, "Z8": 693, "Z9": 715, "Z10": 747, "Z11": 763, "Z12": 788},
        "page": 235
    },
    # Columna 4 cajones Bax + horno + micro + 2 puertas
    {
        "reference": "22HM4CB2P600",
        "name": "Columna 4 cajones Bax + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM4CB2P600",
        "points": 524,
        "zonePoints": {"Z1": 524, "Z2": 526, "Z3": 558, "Z4": 526, "Z5": 558, "Z6": 597, "Z7": 629, "Z8": 636, "Z9": 662, "Z10": 715, "Z11": 740, "Z12": 795},
        "page": 235
    },

    # ========== PÁGINA 236 ==========
    # Columna 4 cajones Lux + horno + micro + 2 puertas
    {
        "reference": "22HM4CL2P600",
        "name": "Columna 4 cajones Lux + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM4CL2P600",
        "points": 629,
        "zonePoints": {"Z1": 629, "Z2": 630, "Z3": 662, "Z4": 631, "Z5": 663, "Z6": 701, "Z7": 733, "Z8": 741, "Z9": 765, "Z10": 820, "Z11": 845, "Z12": 900},
        "page": 236
    },
    # Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta
    {
        "reference": "22HM1G2CB1P600",
        "name": "Columna 1 cacerolero + 2 cajones Bax + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G2CB1P600",
        "points": 445,
        "zonePoints": {"Z1": 445, "Z2": 453, "Z3": 479, "Z4": 470, "Z5": 502, "Z6": 506, "Z7": 531, "Z8": 538, "Z9": 558, "Z10": 615, "Z11": 635, "Z12": 693},
        "page": 236
    },
    # Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta
    {
        "reference": "22HM1G2CL1P600",
        "name": "Columna 1 cacerolero + 2 cajones Lux + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G2CL1P600",
        "points": 530,
        "zonePoints": {"Z1": 530, "Z2": 536, "Z3": 563, "Z4": 555, "Z5": 588, "Z6": 595, "Z7": 623, "Z8": 629, "Z9": 650, "Z10": 696, "Z11": 716, "Z12": 773},
        "page": 236
    },
    # Columna 1 cacerolero + 2 cajones Bax + horno + micro + 2 puertas
    {
        "reference": "22HM1G2CB2P600",
        "name": "Columna 1 cacerolero + 2 cajones Bax + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G2CB2P600",
        "points": 475,
        "zonePoints": {"Z1": 475, "Z2": 483, "Z3": 511, "Z4": 496, "Z5": 528, "Z6": 558, "Z7": 588, "Z8": 574, "Z9": 620, "Z10": 688, "Z11": 716, "Z12": 804},
        "page": 236
    },

    # ========== PÁGINA 237 ==========
    # Columna 1 cacerolero + 2 cajones Lux + horno + micro + 2 puertas
    {
        "reference": "22HM1G2CL2P600",
        "name": "Columna 1 cacerolero + 2 cajones Lux + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G2CL2P600",
        "points": 536,
        "zonePoints": {"Z1": 536, "Z2": 544, "Z3": 571, "Z4": 558, "Z5": 588, "Z6": 629, "Z7": 659, "Z8": 667, "Z9": 691, "Z10": 747, "Z11": 774, "Z12": 858},
        "page": 237
    },
    # Columna 1 cacerolero + 1 cajon Bax + horno + micro + 1 puerta
    {
        "reference": "22HM1G1CB1P600",
        "name": "Columna 1 cacerolero + 1 cajón Bax + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G1CB1P600",
        "points": 414,
        "zonePoints": {"Z1": 414, "Z2": 426, "Z3": 446, "Z4": 438, "Z5": 461, "Z6": 473, "Z7": 494, "Z8": 498, "Z9": 515, "Z10": 548, "Z11": 562, "Z12": 618},
        "page": 237
    },
    # Columna 1 cacerolero + 1 cajon Lux + horno + micro + 1 puerta
    {
        "reference": "22HM1G1CL1P600",
        "name": "Columna 1 cacerolero + 1 cajón Lux + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G1CL1P600",
        "points": 450,
        "zonePoints": {"Z1": 450, "Z2": 452, "Z3": 482, "Z4": 474, "Z5": 497, "Z6": 508, "Z7": 529, "Z8": 533, "Z9": 550, "Z10": 584, "Z11": 597, "Z12": 654},
        "page": 237
    },
    # Columna 1 cacerolero + 1 cajon Bax + horno + micro + 2 puertas
    {
        "reference": "22HM1G1CB2P600",
        "name": "Columna 1 cacerolero + 1 cajón Bax + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G1CB2P600",
        "points": 403,
        "zonePoints": {"Z1": 403, "Z2": 418, "Z3": 444, "Z4": 443, "Z5": 477, "Z6": 496, "Z7": 525, "Z8": 532, "Z9": 555, "Z10": 638, "Z11": 670, "Z12": 792},
        "page": 237
    },

    # ========== PÁGINA 238 ==========
    # Columna 1 cacerolero + 1 cajon Lux + horno + micro + 2 puertas
    {
        "reference": "22HM1G1CL2P600",
        "name": "Columna 1 cacerolero + 1 cajón Lux + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1G1CL2P600",
        "points": 452,
        "zonePoints": {"Z1": 452, "Z2": 465, "Z3": 492, "Z4": 491, "Z5": 524, "Z6": 543, "Z7": 572, "Z8": 580, "Z9": 603, "Z10": 686, "Z11": 718, "Z12": 840},
        "page": 238
    },
    # Columna 1 cacerolero Bax + horno + micro + 1 puerta
    {
        "reference": "22HM1GB1P600",
        "name": "Columna 1 cacerolero Bax + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1GB1P600",
        "points": 378,
        "zonePoints": {"Z1": 378, "Z2": 391, "Z3": 411, "Z4": 402, "Z5": 425, "Z6": 437, "Z7": 458, "Z8": 462, "Z9": 479, "Z10": 512, "Z11": 526, "Z12": 583},
        "page": 238
    },
    # Columna 1 cacerolero Lux + horno + micro + 1 puerta
    {
        "reference": "22HM1GL1P600",
        "name": "Columna 1 cacerolero Lux + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1GL1P600",
        "points": 400,
        "zonePoints": {"Z1": 400, "Z2": 401, "Z3": 432, "Z4": 423, "Z5": 446, "Z6": 458, "Z7": 479, "Z8": 483, "Z9": 500, "Z10": 533, "Z11": 547, "Z12": 641},
        "page": 238
    },
    # Columna 1 cacerolero Bax + horno + micro + 2 puertas
    {
        "reference": "22HM1GB2P600",
        "name": "Columna 1 cacerolero Bax + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1GB2P600",
        "points": 405,
        "zonePoints": {"Z1": 405, "Z2": 418, "Z3": 438, "Z4": 429, "Z5": 453, "Z6": 464, "Z7": 485, "Z8": 489, "Z9": 506, "Z10": 540, "Z11": 553, "Z12": 610},
        "page": 238
    },

    # ========== PÁGINA 239 ==========
    # Columna 1 cacerolero Lux + horno + micro + 2 puertas
    {
        "reference": "22HM1GL2P600",
        "name": "Columna 1 cacerolero Lux + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM1GL2P600",
        "points": 427,
        "zonePoints": {"Z1": 427, "Z2": 428, "Z3": 459, "Z4": 450, "Z5": 474, "Z6": 485, "Z7": 506, "Z8": 510, "Z9": 527, "Z10": 561, "Z11": 574, "Z12": 668},
        "page": 239
    },
    # Columna 2 caceroleros + 1 cajon Bax + horno + micro + 1 puerta
    {
        "reference": "22HM2G1CB1P600",
        "name": "Columna 2 caceroleros + 1 cajón Bax + horno + micro + 1 puerta 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM2G1CB1P600",
        "points": 475,
        "zonePoints": {"Z1": 475, "Z2": 486, "Z3": 518, "Z4": 526, "Z5": 568, "Z6": 573, "Z7": 608, "Z8": 615, "Z9": 643, "Z10": 700, "Z11": 726, "Z12": 822},
        "page": 239
    },
    # Columna 2 caceroleros + 1 cajon Lux + horno + micro + 1 puerta (SIN PRECIOS en la imagen - celdas vacías)
    # Nota: Este producto aparece en la imagen pero las celdas de precios están vacías
    # Lo omitimos hasta tener datos completos
    
    # Columna 2 caceroleros + 1 cajon Bax + horno + micro + 2 puertas
    {
        "reference": "22HM2G1CB2P600",
        "name": "Columna 2 caceroleros + 1 cajón Bax + horno + micro + 2 puertas 600mm Alto 220cm",
        "category": "COLUMNAS",
        "series": "PROGRAMA ESTANDAR",
        "module": "COLUMNA HORNO+MICRO",
        "height": 2200,
        "depth": 580,
        "width": 600,
        "code": "22HM2G1CB2P600",
        "points": 502,
        "zonePoints": {"Z1": 502, "Z2": 517, "Z3": 551, "Z4": 545, "Z5": 587, "Z6": 639, "Z7": 681, "Z8": 691, "Z9": 723, "Z10": 788, "Z11": 821, "Z12": 957},
        "page": 239
    },
]

async def process_products():
    """Insert products into the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db.products
    
    # Count before
    count_before = await products_collection.count_documents({})
    print(f"📊 Productos antes de importar: {count_before}")
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for product in PRODUCTS_PAGES_235_239:
        # Check if product already exists
        existing = await products_collection.find_one({"reference": product["reference"]})
        
        if existing:
            # Update existing product
            result = await products_collection.update_one(
                {"reference": product["reference"]},
                {"$set": {
                    **product,
                    "updatedAt": datetime.utcnow()
                }}
            )
            if result.modified_count > 0:
                updated += 1
                print(f"🔄 Actualizado: {product['reference']} - {product['name'][:50]}...")
            else:
                skipped += 1
        else:
            # Insert new product
            product["createdAt"] = datetime.utcnow()
            product["updatedAt"] = datetime.utcnow()
            await products_collection.insert_one(product)
            inserted += 1
            print(f"✅ Insertado: {product['reference']} - {product['name'][:50]}...")
    
    # Count after
    count_after = await products_collection.count_documents({})
    
    print("\n" + "="*60)
    print(f"📋 RESUMEN DE IMPORTACIÓN - Páginas 235-239")
    print("="*60)
    print(f"✅ Nuevos productos insertados: {inserted}")
    print(f"🔄 Productos actualizados: {updated}")
    print(f"⏭️  Productos sin cambios: {skipped}")
    print(f"📊 Total productos en BD: {count_after}")
    print("="*60)
    
    # Verify the imported products
    print("\n🔍 Verificando productos importados:")
    for product in PRODUCTS_PAGES_235_239:
        found = await products_collection.find_one({"reference": product["reference"]})
        if found:
            print(f"  ✓ {product['reference']}")
        else:
            print(f"  ✗ {product['reference']} - NO ENCONTRADO")
    
    client.close()
    return inserted, updated

if __name__ == "__main__":
    asyncio.run(process_products())
