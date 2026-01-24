#!/usr/bin/env python3
"""
Script completo para importar TODOS los productos desde la tarifa técnica.
"""
import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')

def extract_dimensions_from_code(code):
    """Extrae dimensiones del código del producto."""
    width = 0
    height = 80  # Default para bajos
    depth = 58   # Default estándar
    
    # Extraer ancho del final del código (3 o 4 dígitos)
    width_match = re.search(r'(\d{3,4})$', code)
    if width_match:
        width = int(width_match.group(1))
    
    # Determinar alto basado en código
    # Altos: A35, A45, A70, A80, A90, A13 (130cm)
    if code.startswith('A13'):
        height = 130
    elif code.startswith('A22'):
        height = 220  # Columna despensero
    elif code.startswith('A35'):
        height = 35
    elif code.startswith('A45'):
        height = 45
    elif code.startswith('A70'):
        height = 70
    elif code.startswith('A80') or 'A8' in code:
        height = 80
    elif code.startswith('A90') or 'A9' in code:
        height = 90
    # Bajos
    elif code.startswith('B8') or 'G8B' in code:
        height = 80
    elif code.startswith('B7') or 'G7B' in code:
        height = 70
    elif code.startswith('B6') or 'G6B' in code:
        height = 60
    # Columnas
    elif 'CL' in code or 'COL' in code or 'CP' in code or code.startswith('C'):
        height = 220
    
    # Fondo para altos y columnas
    if code.startswith('A') and not code.startswith('A22'):
        depth = 33
    elif 'CL' in code or 'COL' in code:
        depth = 58
    
    return width, height, depth

def determine_category(code):
    """Determina la categoría basándose en el código."""
    code_upper = code.upper()
    
    # Columnas
    if code_upper.startswith('A22'):
        return 'COLUMNA DESPENSERO'
    if 'CL' in code_upper or 'COL' in code_upper or 'CP' in code_upper:
        if code_upper.startswith('G'):
            return 'COLUMNA GOLA'
        return 'COLUMNA'
    
    # Altos
    if code_upper.startswith('A'):
        if 'GOLA' in code_upper or code_upper.startswith('GA'):
            return 'ALTO GOLA'
        return 'ALTO'
    
    # Bajos GOLA
    if code_upper.startswith('G') and 'B' in code_upper:
        return 'BAJO GOLA'
    
    # Bajos estándar
    if code_upper.startswith('B'):
        return 'BAJO'
    
    return 'OTRO'

def generate_product_name(code, category):
    """Genera un nombre descriptivo para el producto."""
    width, height, depth = extract_dimensions_from_code(code)
    
    features = []
    
    # Puertas
    puertas_match = re.search(r'(\d)P', code)
    if puertas_match:
        num = puertas_match.group(1)
        features.append(f"{num} puerta{'s' if int(num) > 1 else ''}")
    
    # Cajones
    cajones_match = re.search(r'(\d)C(?![LHOP])', code)
    if cajones_match:
        num = cajones_match.group(1)
        features.append(f"{num} cajón{'es' if int(num) > 1 else ''}")
    
    # Tipos especiales
    special_types = {
        'CE': 'ciego',
        'RI': 'rinconero',
        'RIN': 'rinconero',
        'FR': 'fregadero',
        'FRE': 'fregadero',
        'HO': 'horno',
        'HOR': 'horno',
        'MI': 'microondas',
        'MIC': 'microondas',
        'ESC': 'escobero',
        'AB': 'abatible',
        'BI': 'bifacial',
        'EX': 'extraíble',
        'SC': 'semicolumna',
        'CD': 'columna despensa',
        'CH': 'columna horno',
        'GL': 'gavetero lateral',
        'GM': 'gavetero medio',
        'VIT': 'vitrina',
        'CAM': 'campana',
        '1CB': '1 cajón bajo',
        '1CL': '1 cajón lateral',
    }
    
    for key, desc in special_types.items():
        if key in code.upper():
            if desc not in features:
                features.append(desc)
    
    # Serie
    serie = "GOLA" if 'G' in code[:2] else ""
    
    name = category
    if features:
        name += f" {' '.join(features[:3])}"  # Max 3 features
    if width > 0:
        name += f" {width}"
    
    return name

async def import_products():
    """Importa productos desde el archivo de texto extraído."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db['products']
    
    # Leer archivo completo
    with open('/tmp/tarifa_completa.txt', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    products_to_import = []
    
    # Patrones de códigos de productos
    patterns = [
        # GOLA Bajos: G8B1P300, G7B2V600
        re.compile(r'^(G[0-9][AB][A-Z0-9]+\d{3,4})$'),
        # GOLA Columnas: GCL, GCP, GCOL
        re.compile(r'^(GC[LOPR][A-Z0-9]*\d{3,4})$'),
        # Altos estándar: A45A1P300, A80A2P600, A13SC1P400
        re.compile(r'^(A\d{2}[A-Z0-9]+\d{3,4})$'),
        # Bajos estándar: B8B1P300
        re.compile(r'^(B[0-9][A-Z0-9]+\d{3,4})$'),
        # Columnas estándar: CL, CP
        re.compile(r'^(C[LOP][A-Z0-9]*\d{3,4})$'),
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Buscar código de producto
        matched_code = None
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                matched_code = match.group(1)
                break
        
        if matched_code:
            code = matched_code
            
            # Buscar precio en las siguientes líneas
            price = 0
            for j in range(1, 15):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    try:
                        price = float(next_line.replace(',', '.'))
                        if price > 0:
                            break
                    except:
                        continue
            
            category = determine_category(code)
            width, height, depth = extract_dimensions_from_code(code)
            
            # Solo productos con dimensiones válidas
            if width > 0 and width < 2000:
                name = generate_product_name(code, category)
                serie = "GOLA" if code.startswith('G') else "TIRADOR"
                
                products_to_import.append({
                    'code': code,
                    'name': name,
                    'category': category,
                    'width': width,
                    'height': height,
                    'depth': depth,
                    'price': price,
                    'series': serie,
                    'description': f"Mueble {category.lower()} serie {serie}",
                    'imported_at': datetime.utcnow().isoformat(),
                    'source': 'tarifa_tecnica_2025'
                })
        
        i += 1
    
    print(f"Encontrados {len(products_to_import)} productos para importar")
    
    # Eliminar duplicados por código
    unique_products = {}
    for p in products_to_import:
        if p['code'] not in unique_products:
            unique_products[p['code']] = p
    
    products_to_import = list(unique_products.values())
    print(f"Productos únicos: {len(products_to_import)}")
    
    # Importar a MongoDB usando upsert
    imported = 0
    updated = 0
    
    for product in products_to_import:
        result = await products_collection.update_one(
            {'code': product['code']},
            {'$set': product},
            upsert=True
        )
        if result.upserted_id:
            imported += 1
        elif result.modified_count > 0:
            updated += 1
    
    print(f"Importados: {imported} nuevos, {updated} actualizados")
    
    # Mostrar resumen por categoría
    categories = {}
    for p in products_to_import:
        cat = p['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nResumen por categoría:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    # Total en BD
    total_in_db = await products_collection.count_documents({})
    print(f"\nTotal productos en base de datos: {total_in_db}")
    
    client.close()
    return len(products_to_import)

if __name__ == '__main__':
    asyncio.run(import_products())
