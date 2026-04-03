#!/usr/bin/env python3
"""
Script para añadir/actualizar productos de TARIFA 1 Página 6
LATERALES COLOR, REGLETA COLOR, COSTADOS, TECHO COLOR, ELEMENTOS LINEALES
"""
import os
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def create_product(code, name, series, price, width=None, height=None, depth=None, has_hand=False):
    """Create or update a product in MV library"""
    product = {
        'id': str(uuid.uuid4()),
        'code': code,
        'name': name,
        'category': series.upper(),
        'type': 'montada',
        'series': series,
        'visualType': 'COMPLEMENTO',
        'width': width,
        'height': height,
        'depth': depth,
        'manufacturer': 'MV',
        'module': 'montada',
        'library': 'MV',
        'points': float(price),
        'zonePoints': {'T1': float(price)},
        'catalogId': 'mv-catalog',
        'sourceFile': 'TARIFA 1 Pagina 6',
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'updatedAt': datetime.now(timezone.utc).isoformat(),
        'hasHandOption': has_hand
    }
    return product

def update_or_insert(product):
    """Update if exists, insert if not"""
    query = {
        'library': 'MV',
        'code': product['code'],
        'series': product['series']
    }
    if product.get('height'):
        query['height'] = product['height']
    
    existing = db.products.find_one(query)
    if existing:
        db.products.update_one(
            {'_id': existing['_id']},
            {'$set': {
                'points': product['points'],
                'zonePoints': product['zonePoints'],
                'width': product.get('width'),
                'updatedAt': product['updatedAt']
            }}
        )
        return 'updated'
    else:
        db.products.insert_one(product)
        return 'inserted'

# ============================================================================
# PÁGINA 6: LATERALES COLOR, REGLETA, COSTADOS, TECHO, ELEMENTOS LINEALES
# ============================================================================

products_to_add = []

# LATERALES COLOR (Ancho 15)
laterales_color = [
    ('LCA', 'Lateral color alto', 10, 70),
    ('LCA', 'Lateral color alto', 11, 90),
    ('LCB', 'Lateral color bajo', 14, 70),
    ('LCB', 'Lateral color bajo', 16, 90),
    ('LCF', 'Lateral color caldera', 15, 70),
    ('LCF', 'Lateral color caldera', 22, 90),
    ('LCS', 'Lateral color sobreencimera', 15, 70),
    ('LCS', 'Lateral color sobreencimera', 18, 90),
    ('LCM', 'Lateral color mediacolumna', 18, 70),
    ('LCM', 'Lateral color mediacolumna', 22, 90),
    ('LCC', 'Lateral color columna', 31, 70),
    ('LCC', 'Lateral color columna', 33, 90),
]

for code, name, price, height in laterales_color:
    p = create_product(code, f'{name} H{height}', 'LATERALES COLOR', price, width=15, height=height)
    products_to_add.append(p)

# REGLETA COLOR (Ancho 15)
regleta_color = [
    ('RA', 'Regleta color alto', 4, 70),
    ('RA', 'Regleta color alto', 5, 90),
    ('RMV', 'Regleta color canto mediacolumna', 5, 70),
    ('RMV', 'Regleta color canto mediacolumna', 8, 90),
    ('RS', 'Regleta color canto sobreencimera', 7, 70),
    ('RS', 'Regleta color canto sobreencimera', 8, 90),
    ('RC', 'Regleta color canto columna', 11, 70),
    ('RC', 'Regleta color canto columna', 12, 90),
]

for code, name, price, height in regleta_color:
    p = create_product(code, f'{name} H{height}', 'REGLETA COLOR', price, width=15, height=height)
    products_to_add.append(p)

# COSTADOS MELAMINA (Ancho 10)
costados_melamina = [
    ('CMBB', 'Costado melamina bajo blanco', 7, 70),
    ('CMBB', 'Costado melamina bajo blanco', 8, 90),
    ('CNCC', 'Costado melamina columna color', 26, 70),
    ('CNCC', 'Costado melamina columna color', 27, 90),
    ('CMCB', 'Costado melamina columna blanco', 19, 70),
    ('CMCB', 'Costado melamina columna blanco', 20, 90),
]

for code, name, price, height in costados_melamina:
    p = create_product(code, f'{name} H{height}', 'COSTADOS MELAMINA', price, width=10, height=height)
    products_to_add.append(p)

# COSTADOS COLOR (Ancho 10)
costados_color = [
    ('CCF', 'Costado color alto 70/90 alto', 14, 70),
    ('CCF', 'Costado color alto 70/90 alto', 9, 90),
    ('CCS', 'Costado color sobreencimera', 14, 70),
    ('CCS', 'Costado color sobreencimera', 15, 90),
    ('CCM', 'Costado color mediacolumna', 17, 70),
    ('CCM', 'Costado color mediacolumna', 21, 90),
    ('CCC', 'Costado color columna', 50, 70),
    ('CCC', 'Costado color columna', 36, 90),
]

for code, name, price, height in costados_color:
    p = create_product(code, f'{name} H{height}', 'COSTADOS COLOR', price, width=10, height=height)
    products_to_add.append(p)

# REGLETA MELAMINA (Ancho 10)
regleta_melamina = [
    ('RMA', 'Regleta melamina alto', 1, 70),
    ('RMA', 'Regleta melamina alto', 3, 90),
    ('RMM', 'Regleta melamina mediacolumna', 4, 70),
    ('RMM', 'Regleta melamina mediacolumna', 5, 90),
    ('RMS', 'Regleta melamina sobreencimera', 3, 70),
    ('RMS', 'Regleta melamina sobreencimera', 4, 90),
]

for code, name, price, height in regleta_melamina:
    p = create_product(code, f'{name} H{height}', 'REGLETA MELAMINA', price, width=10, height=height)
    products_to_add.append(p)

# TECHO COLOR (diferentes anchos: 100-360)
techo_color = [
    ('TEC100', 'Cornisa entera/media', 14.4, 100),
    ('TEC120', 'Cornisa entera/media', 15.4, 120),
    ('TEC140', 'Cornisa entera/media', 16.4, 140),
    ('TEC160', 'Cornisa entera/media', 17.4, 160),
    ('TEC180', 'Cornisa entera/media', 19.4, 180),
    ('TEC200', 'Cornisa entera/media', 20.4, 200),
    ('TEC220', 'Cornisa entera/media', 25.4, 220),
    ('TEC240', 'Cornisa entera/media', 27.4, 240),
    ('TEC260', 'Cornisa entera/media', 29.4, 260),
    ('TEC280', 'Cornisa entera/media', 31.4, 280),
    ('TEC300', 'Cornisa entera/media', 33.4, 300),
    ('TEC320', 'Cornisa entera/media', 34.4, 320),
    ('TEC340', 'Cornisa entera/media', 38.4, 340),
    ('TEC360', 'Cornisa entera/media', 35.4, 360),
]

for code, name, price, width in techo_color:
    p = create_product(code, f'{name} {width}cm', 'TECHO COLOR', price, width=width)
    products_to_add.append(p)

# ELEMENTOS LINEALES (precios fijos, sin altura)
elementos_lineales = [
    ('COR', 'Cornisa entera/media', 2, None),
    ('POR', 'Portaluz entera/medio', 2, None),
    ('ZOC', 'Zócalo entera/medio', 3, None),
    ('PIN', 'Perfil pintor entera/medio', 3, None),
    ('ZOCAB', 'Juego 3 piezas zócalo', 21, None),
    ('ZONA', 'Zócalo aluminio entera/medio', 18, None),
    ('ANGZOC', 'Ángulo zócalo aluminio', 3, None),
    ('ANST', 'Costadillo campana aluminio', 28, None),
    ('PINGZOC', 'Juego zócalo zócalo aluminio', 34, None),
    ('COST', 'Costadillo campana unidad', 16, None),
    ('ENCM/E', 'Encimera Md/Ent', 2, None),
    ('EMC1M/E', 'Encimera Md/Ent', 4, None),
    ('MOSE', 'Mostrador solo Entero', 85, None),
    ('MOSG/TLIN', 'T unión Angular/Linea', 3, None),
    ('UPMC', 'U terminacion encimera', 29, None),
    ('COPM/E', 'Copete Med/Entero', 10, None),
    ('INT/EXT', 'Interior/Exterior copete', 1, None),
    ('TAPAC', 'Juego tapas copete', 18, None),
    ('TCAN', 'Tira cantos encimera', 1, None),
]

for code, name, price, _ in elementos_lineales:
    p = create_product(code, name, 'ELEMENTOS LINEALES', price)
    products_to_add.append(p)

# Ejecutar inserción/actualización
print("=" * 60)
print("AÑADIENDO PRODUCTOS PÁGINA 6 - TARIFA 1")
print("=" * 60)

inserted = 0
updated = 0

for product in products_to_add:
    result = update_or_insert(product)
    if result == 'inserted':
        inserted += 1
        print(f"  + {product['code']} ({product['series']}): {product['points']} PTS")
    else:
        updated += 1
        print(f"  ~ {product['code']} ({product['series']}): {product['points']} PTS (actualizado)")

print()
print("=" * 60)
print(f"TOTAL INSERTADOS: {inserted}")
print(f"TOTAL ACTUALIZADOS: {updated}")
print(f"TOTAL PROCESADOS: {inserted + updated}")
print("=" * 60)

# Verificar total de productos MV
total_mv = db.products.count_documents({'library': 'MV'})
print(f"\nTOTAL PRODUCTOS MV EN BASE DE DATOS: {total_mv}")
