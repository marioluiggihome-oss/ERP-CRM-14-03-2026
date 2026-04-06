#!/usr/bin/env python3
"""
Script completo para importar TODOS los productos desde la tarifa técnica.
Incluye ALTOS, BAJOS, COLUMNAS, series GOLA y estándar.
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
    height = 80
    depth = 58
    
    # Extraer ancho - puede tener formato especial como 60300 (60cm fondo, 300 ancho)
    # Primero buscar los últimos 3-4 dígitos
    width_match = re.search(r'(\d{3,4})$', code)
    if width_match:
        w = int(width_match.group(1))
        # Si el ancho parece incluir el fondo (ej: 60300 = fondo 60, ancho 300)
        if w > 1000 and w < 100000:
            width = w % 1000  # Tomar los últimos 3 dígitos
        else:
            width = w
    
    # Determinar alto basado en código
    code_upper = code.upper()
    
    # ALTOS - detectar por prefijo
    if code_upper.startswith('A13'):
        height = 130
    elif code_upper.startswith('A22'):
        height = 220
    elif code_upper.startswith('A35'):
        height = 35
    elif code_upper.startswith('A45'):
        height = 45
    elif code_upper.startswith('A7') or code_upper.startswith('A70'):
        height = 70
    elif code_upper.startswith('A8') or code_upper.startswith('A80'):
        height = 80
    elif code_upper.startswith('A9') or code_upper.startswith('A90'):
        height = 90
    # BAJOS
    elif 'G8B' in code_upper or code_upper.startswith('B8'):
        height = 80
    elif 'G7B' in code_upper or code_upper.startswith('B7'):
        height = 70
    elif 'G6B' in code_upper or code_upper.startswith('B6'):
        height = 60
    # COLUMNAS
    elif 'CL' in code_upper or 'COL' in code_upper or 'CP' in code_upper:
        height = 220
    elif code_upper.startswith('C22') or code_upper.startswith('C20'):
        height = 220
    
    # FONDO
    if code_upper.startswith('A') and not code_upper.startswith('A22'):
        depth = 33
    elif 'F60' in code_upper or '60' in code_upper[:6]:
        depth = 60
    elif 'F35' in code_upper:
        depth = 35
    
    return width, height, depth

def determine_category(code):
    """Determina la categoría basándose en el código."""
    code_upper = code.upper()
    
    # COLUMNAS
    if code_upper.startswith('A22') or code_upper.startswith('C22'):
        return 'COLUMNA DESPENSERO'
    if code_upper.startswith('GC') or (code_upper.startswith('G') and ('CL' in code_upper or 'COL' in code_upper)):
        return 'COLUMNA GOLA'
    if 'CL' in code_upper or 'COL' in code_upper or 'CP' in code_upper or code_upper.startswith('C2'):
        return 'COLUMNA'
    
    # ALTOS GOLA (G7A, G8A, G9A, etc.)
    if re.match(r'^G\d+A', code_upper):
        return 'ALTO GOLA'
    
    # ALTOS estándar
    if code_upper.startswith('A'):
        return 'ALTO'
    
    # BAJOS GOLA (G7B, G8B, etc.)
    if re.match(r'^G\d+B', code_upper):
        return 'BAJO GOLA'
    
    # BAJOS estándar
    if code_upper.startswith('B'):
        return 'BAJO'
    
    return 'OTRO'

def generate_product_name(code, category):
    """Genera un nombre descriptivo para el producto."""
    width, height, depth = extract_dimensions_from_code(code)
    
    features = []
    code_upper = code.upper()
    
    # Puertas
    puertas_match = re.search(r'(\d)P(?!ABL)', code_upper)
    if puertas_match:
        num = int(puertas_match.group(1))
        features.append(f"{num} puerta{'s' if num > 1 else ''}")
    
    # Cajones
    if '4C' in code_upper:
        features.append("4 cajones")
    elif '3C' in code_upper:
        features.append("3 cajones")
    elif '2C' in code_upper:
        features.append("2 cajones")
    elif re.search(r'1C(?![LHOP])', code_upper):
        features.append("1 cajón")
    
    # Tipos especiales
    if 'ABL' in code_upper or 'AB' in code_upper:
        features.append("abatible")
    if 'SC' in code_upper:
        features.append("semicolumna")
    if 'CD' in code_upper:
        features.append("despensa")
    if 'CH' in code_upper:
        features.append("horno")
    if 'CM' in code_upper or 'CHM' in code_upper:
        features.append("horno+micro")
    if 'GL' in code_upper:
        features.append("gavetero")
    if 'CE' in code_upper:
        features.append("ciego")
    if 'RI' in code_upper:
        features.append("rinconero")
    if 'FR' in code_upper:
        features.append("fregadero")
    if 'HO' in code_upper and 'CHO' not in code_upper:
        features.append("horno")
    if 'MIC' in code_upper or 'MI' in code_upper:
        features.append("microondas")
    if 'VIT' in code_upper or 'V' == code_upper[-4:-3]:
        features.append("vitrina")
    
    name = category
    if features:
        name += f" {' '.join(features[:3])}"
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
        (re.compile(r'^(G[0-9][AB][A-Z0-9]+\d{3,4})$'), 'GOLA'),
        # GOLA Columnas: GCL, GCP, GCOL
        (re.compile(r'^(GC[LOPR][A-Z0-9]*\d{3,4})$'), 'GOLA'),
        # Altos: A7A1P300, A8A2P600, A45A1P300, A13SC1P400
        (re.compile(r'^(A\d{1,2}[A-Z0-9]+\d{3,4})$'), 'TIRADOR'),
        # Bajos: B8B1P300, B71P400
        (re.compile(r'^(B[0-9][A-Z0-9]+\d{3,4})$'), 'TIRADOR'),
        # Columnas: C22, C20
        (re.compile(r'^(C\d{2}[A-Z0-9]*\d{3,4})$'), 'TIRADOR'),
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Limpiar línea de caracteres extraños
        line = re.sub(r'\s+', '', line)
        
        # Buscar código de producto
        matched_code = None
        serie = 'TIRADOR'
        for pattern, s in patterns:
            match = pattern.match(line)
            if match:
                matched_code = match.group(1)
                serie = s
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
                        if price > 0 and price < 10000:  # Precio razonable
                            break
                    except:
                        continue
            
            category = determine_category(code)
            width, height, depth = extract_dimensions_from_code(code)
            
            # Solo productos con dimensiones válidas
            if width > 0 and width < 2000 and height > 0:
                name = generate_product_name(code, category)
                
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
    
    # Ejemplos por categoría
    print("\nEjemplos por categoría:")
    for cat in sorted(categories.keys()):
        examples = [p for p in products_to_import if p['category'] == cat][:3]
        for p in examples:
            print(f"  {p['code']}: {p['name']} - {p['width']}x{p['height']}x{p['depth']} - {p['price']}€")
    
    client.close()
    return len(products_to_import)

if __name__ == '__main__':
    asyncio.run(import_products())
