# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
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
    1. Si no tiene height definido o height=0, crear variantes 200 y 220
    2. Eliminar el producto original sin altura
    """
    products_collection = db['products']
    
    # Buscar todos los productos COLUMNA de la biblioteca MV SIN variante de altura
    columnas = list(products_collection.find({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES},
        'code': {'$not': {'$regex': '/(200|220)$'}}  # Excluir los que ya tienen /200 o /220
    }))
    
    print(f"Encontradas {len(columnas)} columnas MV originales (sin variante de altura)")
    
    products_to_insert = []
    products_to_delete = []
    
    for col in columnas:
        base_code = col.get('code', '')
        base_name = col.get('name', '')
        
        # Verificar si ya existen variantes
        existing_200 = products_collection.find_one({
            'library': 'MV',
            'code': f"{base_code}/200"
        })
        existing_220 = products_collection.find_one({
            'library': 'MV', 
            'code': f"{base_code}/220"
        })
        
        # Crear variante altura 200 si no existe
        if not existing_200:
            variant_200 = {
                **{k: v for k, v in col.items() if k != '_id'},
                'code': f"{base_code}/200",
                'name': f"{base_name} H200",
                'height': 200,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            products_to_insert.append(variant_200)
        
        # Crear variante altura 220 si no existe
        if not existing_220:
            variant_220 = {
                **{k: v for k, v in col.items() if k != '_id'},
                'code': f"{base_code}/220",
                'name': f"{base_name} H220",
                'height': 220,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            products_to_insert.append(variant_220)
        
        # Marcar el producto original para eliminación
        products_to_delete.append(col['_id'])
    
    # Insertar nuevas variantes
    if products_to_insert:
        print(f"\nInsertando {len(products_to_insert)} variantes de altura...")
        for p in products_to_insert[:10]:  # Mostrar solo los primeros 10
            print(f"  + {p['code']}: {p['name']} (H={p['height']})")
        if len(products_to_insert) > 10:
            print(f"  ... y {len(products_to_insert) - 10} más")
        
        result = products_collection.insert_many(products_to_insert)
        print(f"Insertados {len(result.inserted_ids)} productos")
    
    # Eliminar productos originales sin altura definida
    if products_to_delete:
        print(f"\nEliminando {len(products_to_delete)} productos originales sin altura...")
        for pid in products_to_delete:
            products_collection.delete_one({'_id': pid})
        print(f"Eliminados {len(products_to_delete)} productos")
    
    # Mostrar resumen
    final_count = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES}
    })
    print(f"\n✅ Total columnas MV después de actualización: {final_count}")
    
    # Mostrar desglose por altura
    count_200 = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES},
        'height': 200
    })
    count_220 = products_collection.count_documents({
        'library': 'MV',
        'category': {'$in': COLUMNA_CATEGORIES},
        'height': 220
    })
    print(f"  - Variantes H200: {count_200}")
    print(f"  - Variantes H220: {count_220}")

if __name__ == '__main__':
    print("=" * 60)
    print("AÑADIENDO VARIANTES DE ALTURA A COLUMNAS MV")
    print("=" * 60)
    add_height_variants()
    print("\n¡Proceso completado!")
