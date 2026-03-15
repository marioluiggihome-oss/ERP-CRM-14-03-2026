"""
Script para añadir variantes de altura a las COLUMNAS de la biblioteca MV
Las columnas deben existir en dos variantes: altura 200 y altura 220
"""
import os
import pymongo
from datetime import datetime, timezone

# Conexión MongoDB usando la variable de entorno
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')

client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]

# Categorías que son COLUMNAS (incluye todas las variantes)
COLUMNA_CATEGORIES = [
    'COLUMNA',
    'COLUMNA_DESPENSERO',
    'COLUMNA_ESCOBERO', 
    'COLUMNA_HORNO',
    'COLUMNA_HORNO_MICRO',
    'COLUMNA_FRIGO',
]

def add_height_variants():
    """
    Para cada producto de tipo COLUMNA en la biblioteca MV:
    1. Si no tiene height definido, crear dos variantes (200 y 220)
    2. Si ya tiene height, verificar que existan ambas variantes
    """
    products_collection = db['products']
    
    # Buscar todos los productos COLUMNA de la biblioteca MV
    columnas = list(products_collection.find({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES}
    }))
    
    print(f"Encontradas {len(columnas)} columnas MV")
    
    products_to_insert = []
    products_to_update = []
    
    # Agrupar por código base (sin el sufijo de altura)
    existing_codes_by_height = {}
    for col in columnas:
        code = col.get('code', '')
        height = col.get('height', 0)
        if code not in existing_codes_by_height:
            existing_codes_by_height[code] = {}
        existing_codes_by_height[code][height] = col
    
    # Procesar cada columna única
    processed_base_codes = set()
    
    for col in columnas:
        base_code = col.get('code', '')
        
        # Evitar procesar el mismo código base múltiples veces
        if base_code in processed_base_codes:
            continue
        processed_base_codes.add(base_code)
        
        heights_present = existing_codes_by_height.get(base_code, {})
        
        # Si el producto no tiene height o tiene height=0, crear ambas variantes
        if 0 in heights_present or len(heights_present) == 0:
            original = heights_present.get(0, col)
            
            # Crear variante altura 200
            if 200 not in heights_present:
                variant_200 = {
                    **{k: v for k, v in original.items() if k != '_id'},
                    'code': f"{base_code}/200",
                    'name': f"{original.get('name', '')} H200",
                    'height': 200,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                products_to_insert.append(variant_200)
            
            # Crear variante altura 220
            if 220 not in heights_present:
                variant_220 = {
                    **{k: v for k, v in original.items() if k != '_id'},
                    'code': f"{base_code}/220",
                    'name': f"{original.get('name', '')} H220",
                    'height': 220,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                products_to_insert.append(variant_220)
            
            # Marcar el producto original con height=0 para eliminarlo después
            if 0 in heights_present:
                products_to_update.append(original['_id'])
        
        # Si ya tiene altura específica pero falta alguna variante
        elif 200 in heights_present and 220 not in heights_present:
            original = heights_present[200]
            variant_220 = {
                **{k: v for k, v in original.items() if k != '_id'},
                'code': base_code.replace('/200', '/220') if '/200' in base_code else f"{base_code}/220",
                'name': original.get('name', '').replace('H200', 'H220') if 'H200' in original.get('name', '') else f"{original.get('name', '')} H220",
                'height': 220,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            products_to_insert.append(variant_220)
            
        elif 220 in heights_present and 200 not in heights_present:
            original = heights_present[220]
            variant_200 = {
                **{k: v for k, v in original.items() if k != '_id'},
                'code': base_code.replace('/220', '/200') if '/220' in base_code else f"{base_code}/200",
                'name': original.get('name', '').replace('H220', 'H200') if 'H220' in original.get('name', '') else f"{original.get('name', '')} H200",
                'height': 200,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            products_to_insert.append(variant_200)
    
    # Insertar nuevas variantes
    if products_to_insert:
        print(f"\nInsertando {len(products_to_insert)} variantes de altura...")
        for p in products_to_insert:
            print(f"  + {p['code']}: {p['name']} (H={p['height']})")
        
        result = products_collection.insert_many(products_to_insert)
        print(f"Insertados {len(result.inserted_ids)} productos")
    
    # Eliminar productos originales sin altura definida (si hay variantes)
    if products_to_update:
        print(f"\nEliminando {len(products_to_update)} productos originales sin altura...")
        for pid in products_to_update:
            products_collection.delete_one({'_id': pid})
        print(f"Eliminados {len(products_to_update)} productos")
    
    # Mostrar resumen
    final_count = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES}
    })
    print(f"\n✅ Total columnas MV después de actualización: {final_count}")

if __name__ == '__main__':
    print("=" * 60)
    print("AÑADIENDO VARIANTES DE ALTURA A COLUMNAS MV")
    print("=" * 60)
    add_height_variants()
    print("\n¡Proceso completado!")
