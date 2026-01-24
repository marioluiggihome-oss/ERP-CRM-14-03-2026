#!/usr/bin/env python3
"""
Script mejorado para importar productos GOLA y otros muebles desde la tarifa técnica.
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
    
    # Determinar alto basado en prefijo
    if '8B' in code or '8A' in code:
        height = 80
    elif '7B' in code or '7A' in code:
        height = 70
    elif '6B' in code or '6A' in code:
        height = 60
    elif 'CL' in code or 'COL' in code or 'CP' in code:
        height = 220  # Columnas
    
    # Fondo para altos
    if 'A' in code and 'B' not in code:
        depth = 33
    
    return width, height, depth

def determine_category(code):
    """Determina la categoría basándose en el código."""
    code_upper = code.upper()
    
    # Columnas
    if 'CL' in code_upper or 'COL' in code_upper or 'CP' in code_upper:
        if code_upper.startswith('G'):
            return 'COLUMNA GOLA'
        return 'COLUMNA'
    
    # Altos
    if 'A' in code_upper and 'B' not in code_upper:
        if code_upper.startswith('G'):
            return 'ALTO GOLA'
        return 'ALTO'
    
    # Bajos
    if 'B' in code_upper:
        if code_upper.startswith('G'):
            return 'BAJO GOLA'
        return 'BAJO'
    
    return 'OTRO'

def generate_product_name(code, category):
    """Genera un nombre descriptivo para el producto."""
    width, height, depth = extract_dimensions_from_code(code)
    
    # Determinar características
    features = []
    
    # Puertas y cajones
    if '1P' in code:
        features.append("1 puerta")
    elif '2P' in code:
        features.append("2 puertas")
    elif '3P' in code:
        features.append("3 puertas")
    
    if '4C' in code:
        features.append("4 cajones")
    elif '3C' in code:
        features.append("3 cajones")
    elif '2C' in code:
        features.append("2 cajones")
    elif '1C' in code and '1CL' not in code and '1CB' not in code:
        features.append("1 cajón")
    
    # Tipos especiales
    if '1CB' in code:
        features.append("1 cajón bajo")
    if '1CL' in code:
        features.append("1 cajón lateral")
    if 'CE' in code:
        features.append("ciego")
    if 'RI' in code or 'RIN' in code:
        features.append("rinconero")
    if 'FR' in code or 'FRE' in code:
        features.append("fregadero")
    if 'HO' in code or 'HOR' in code:
        features.append("horno")
    if 'MI' in code or 'MIC' in code:
        features.append("microondas")
    if 'ESC' in code:
        features.append("escobero")
    if 'AB' in code:
        features.append("abatible")
    if 'V' in code and 'VI' not in code:
        features.append("vitrina")
    
    # Serie
    serie = "GOLA" if code.startswith('G') else "TIRADOR"
    
    name = f"{category}"
    if features:
        name += f" {' '.join(features)}"
    if width > 0:
        name += f" {width}"
    
    return name

async def import_products():
    """Importa productos desde el archivo de texto extraído."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db['products']
    
    # Leer archivo
    with open('/tmp/tarifa_full.txt', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    products_to_import = []
    
    # Patrón para códigos de productos GOLA
    # G8B1P300, G8B2V600, G8A1P400, etc.
    code_pattern = re.compile(r'^(G[0-9][AB][A-Z0-9]+\d{3,4})$')
    
    # También buscar códigos estándar (no GOLA)
    standard_pattern = re.compile(r'^([AB][0-9][A-Z0-9]+\d{3,4})$')
    
    # Columnas
    columna_pattern = re.compile(r'^(G?C[LOP][A-Z0-9]*\d{3,4})$')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Buscar código de producto
        match = code_pattern.match(line) or standard_pattern.match(line) or columna_pattern.match(line)
        
        if match:
            code = match.group(1)
            
            # Buscar precio en las siguientes líneas
            price = 0
            for j in range(1, 15):  # Buscar en las próximas 15 líneas
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    # El primer número después del código es el precio Z1
                    try:
                        price = float(next_line.replace(',', '.'))
                        break
                    except:
                        continue
            
            category = determine_category(code)
            width, height, depth = extract_dimensions_from_code(code)
            
            # Solo productos con dimensiones válidas
            if width > 0:
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
    
    # Mostrar algunos ejemplos
    print("\nEjemplos de productos importados:")
    for p in products_to_import[:10]:
        print(f"  {p['code']}: {p['name']} - {p['width']}x{p['height']}x{p['depth']} - {p['price']}€")
    
    client.close()
    return len(products_to_import)

if __name__ == '__main__':
    asyncio.run(import_products())
