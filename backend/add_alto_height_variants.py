# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Script para crear variantes de altura H90 para productos ALTO de la biblioteca MV
Los productos ALTO deben existir en variantes H70 (ya existen) y H90 (nuevas)
"""
import os
import pymongo
from datetime import datetime, timezone

# Conexión MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')

client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]

# Categorías que son ALTO (incluye todas las variantes)
ALTO_CATEGORIES = [
    'ALTO',
    'ALTO_CALDERA',
    'ALTO_CALENTADOR', 
    'ALTO_CAMPANA',
    'ALTO_DECORATIVO',
    'ALTO_ESCURREPLATOS',
    'ALTO_MICROONDAS',
    'ALTO_RINCON',
    'ALTO_SOBREFRIGO',
    'ALTO_TERMINAL',
    'ALTO_VITRINA',
    'ALTILLO',
    'ALTILLO_DECORATIVO',
    'ALTILLO_VITRINA',
]

def add_height_90_variants():
    """
    Para cada producto ALTO MV con height=70, crear una variante con height=90
    Los puntos para H90 se toman de la columna "90" de la tarifa (1.1x de T1)
    """
    products_collection = db['products']
    
    # Buscar productos ALTO MV con height=70
    altos_h70 = list(products_collection.find({
        'library': 'MV',
        'category': {'$in': ALTO_CATEGORIES},
        'height': 70
    }))
    
    print(f"Encontrados {len(altos_h70)} productos ALTO MV con H=70")
    
    products_to_insert = []
    
    for alto in altos_h70:
        base_code = alto.get('code', '')
        
        # Verificar si ya existe variante H90
        existing_h90 = products_collection.find_one({
            'library': 'MV',
            'code': f"{base_code}/90" if '/70' not in base_code else base_code.replace('/70', '/90')
        })
        
        if existing_h90:
            print(f"  Ya existe variante H90 para {base_code}")
            continue
        
        # Calcular los zonePoints para H90 (multiplicar T1 por 1.1 aproximadamente)
        zone_points = alto.get('zonePoints', {})
        zone_points_90 = {}
        
        for key, value in zone_points.items():
            if isinstance(value, (int, float)):
                # Los precios de H90 son aproximadamente 10% más que H70
                zone_points_90[key] = round(value * 1.1, 1)
        
        # Crear variante H90
        new_code = f"{base_code}/90" if '/70' not in base_code else base_code.replace('/70', '/90')
        variant_90 = {
            **{k: v for k, v in alto.items() if k != '_id'},
            'code': new_code,
            'name': f"{alto.get('name', '')} H90" if 'H70' not in alto.get('name', '') else alto.get('name', '').replace('H70', 'H90'),
            'height': 90,
            'zonePoints': zone_points_90 if zone_points_90 else zone_points,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        products_to_insert.append(variant_90)
    
    # Insertar variantes
    if products_to_insert:
        print(f"\nInsertando {len(products_to_insert)} variantes H90...")
        for p in products_to_insert[:10]:
            print(f"  + {p['code']}: {p['name']}")
        if len(products_to_insert) > 10:
            print(f"  ... y {len(products_to_insert) - 10} más")
        
        result = products_collection.insert_many(products_to_insert)
        print(f"Insertados {len(result.inserted_ids)} productos")
    else:
        print("\nNo hay nuevas variantes para insertar")
    
    # También actualizar los productos H70 existentes para añadir /70 al código si no lo tienen
    print("\n--- Actualizando códigos H70 para clarificar ---")
    updated_count = 0
    for alto in altos_h70:
        code = alto.get('code', '')
        if '/70' not in code and '/90' not in code:
            new_code = f"{code}/70"
            new_name = f"{alto.get('name', '')} H70" if 'H70' not in alto.get('name', '') and 'H90' not in alto.get('name', '') else alto.get('name', '')
            products_collection.update_one(
                {'_id': alto['_id']},
                {'$set': {'code': new_code, 'name': new_name}}
            )
            updated_count += 1
    
    if updated_count:
        print(f"Actualizados {updated_count} productos H70 con código /70")
    
    # Mostrar resumen
    final_count_70 = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': ALTO_CATEGORIES},
        'height': 70
    })
    final_count_90 = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': ALTO_CATEGORIES},
        'height': 90
    })
    print(f"\n✅ Resumen productos ALTO MV:")
    print(f"  - Variantes H70: {final_count_70}")
    print(f"  - Variantes H90: {final_count_90}")

if __name__ == '__main__':
    print("=" * 60)
    print("CREANDO VARIANTES H90 PARA PRODUCTOS ALTO MV")
    print("=" * 60)
    add_height_90_variants()
    print("\n¡Proceso completado!")
