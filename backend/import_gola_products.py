#!/usr/bin/env python3
"""
Script para importar productos GOLA y otros muebles desde la tarifa técnica.
"""
import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')

# Categorías y sus patrones
CATEGORY_PATTERNS = {
    'BAJO GOLA': ['G8B', 'G7B', 'GBF', 'GBFC', 'GBC', 'GBCF', 'GBCE', 'GBR', 'GBRF'],
    'ALTO GOLA': ['G8A', 'G7A', 'GAF', 'GAFC', 'GAC', 'GACF', 'GACE', 'GAR', 'GARF'],
    'COLUMNA GOLA': ['GCL', 'GCP', 'GCO', 'GCOL'],
    'BAJO': ['B8', 'B7', 'BF', 'BC', 'BR'],
    'ALTO': ['A8', 'A7', 'AF', 'AC', 'AR'],
    'COLUMNA': ['CL', 'CP', 'CO', 'COL'],
}

def parse_product_line(line):
    """Parsea una línea de producto."""
    # Patrón típico: CODIGO PRECIO1 PRECIO2 ...
    parts = line.strip().split()
    if not parts:
        return None
    
    code = parts[0]
    
    # Verificar si es un código de producto válido
    if not re.match(r'^[A-Z0-9]+$', code):
        return None
    
    # Extraer precios (números)
    prices = []
    for p in parts[1:]:
        try:
            price = float(p.replace(',', '.'))
            prices.append(price)
        except:
            pass
    
    if not prices:
        return None
    
    # Usar el precio de la zona Z1 (primer precio)
    base_price = prices[0] if prices else 0
    
    return {
        'code': code,
        'base_price': base_price,
        'zone_prices': prices
    }

def extract_dimensions_from_code(code):
    """Extrae dimensiones del código del producto."""
    # Patrones comunes:
    # G8B1P300 -> Alto 80, 1 puerta, ancho 300
    # G7B2P600 -> Alto 70, 2 puertas, ancho 600
    
    width = 0
    height = 80  # Default para bajos
    depth = 58   # Default estándar
    
    # Extraer ancho del final del código
    width_match = re.search(r'(\d{3,4})$', code)
    if width_match:
        width = int(width_match.group(1))
    
    # Determinar alto basado en prefijo
    if 'G8' in code or 'B8' in code or 'A8' in code:
        if 'A' in code:  # Alto
            height = 80
        else:  # Bajo
            height = 80
    elif 'G7' in code or 'B7' in code or 'A7' in code:
        height = 70
    elif 'CL' in code or 'COL' in code:
        height = 220  # Columnas
    
    # Fondo para altos
    if any(x in code for x in ['GA', 'A8', 'A7']):
        depth = 33
    
    return width, height, depth

def determine_category(code):
    """Determina la categoría basándose en el código."""
    code_upper = code.upper()
    
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if code_upper.startswith(pattern):
                return category
    
    # Categorías por contenido del código
    if 'COL' in code_upper or 'CL' in code_upper:
        return 'COLUMNA'
    elif 'B' in code_upper and not 'A' in code_upper:
        return 'BAJO'
    elif 'A' in code_upper:
        return 'ALTO'
    
    return 'OTRO'

def generate_product_name(code, category):
    """Genera un nombre descriptivo para el producto."""
    width, height, depth = extract_dimensions_from_code(code)
    
    # Determinar tipo de puerta
    doors = ""
    if '1P' in code:
        doors = "1 puerta"
    elif '2P' in code:
        doors = "2 puertas"
    elif '3P' in code:
        doors = "3 puertas"
    elif '4C' in code:
        doors = "4 cajones"
    elif '3C' in code:
        doors = "3 cajones"
    elif '2C' in code:
        doors = "2 cajones"
    elif '1C' in code:
        doors = "1 cajón"
    elif 'FC' in code:
        doors = "fregadero cajón"
    elif 'FR' in code or 'FRE' in code:
        doors = "fregadero"
    elif 'HOR' in code:
        doors = "horno"
    elif 'MIC' in code:
        doors = "microondas"
    elif 'FRI' in code:
        doors = "frigorífico"
    elif 'ESC' in code:
        doors = "escobero"
    elif 'RIN' in code:
        doors = "rinconero"
    
    # Serie
    serie = "GOLA" if code.startswith('G') else "TIRADOR"
    
    name = f"{category} {serie}"
    if doors:
        name += f" {doors}"
    if width > 0:
        name += f" {width}mm"
    
    return name

async def import_products():
    """Importa productos desde el archivo de texto extraído."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db['products']
    
    # Leer archivo
    with open('/tmp/tarifa_full.txt', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    products_to_import = []
    current_category = None
    current_description = ""
    
    # Patrones para detectar secciones
    section_patterns = [
        (r'BAJOS', 'BAJO'),
        (r'ALTOS', 'ALTO'),
        (r'COLUMNAS', 'COLUMNA'),
        (r'GOLA', 'GOLA'),
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detectar cambio de sección
        for pattern, cat in section_patterns:
            if pattern in line.upper() and len(line) < 100:
                if 'GOLA' in line.upper():
                    current_description = "GOLA"
                break
        
        # Intentar parsear como producto
        product = parse_product_line(line)
        if product and len(product['code']) >= 6:
            code = product['code']
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
                    'price': product['base_price'],
                    'series': serie,
                    'description': f"Mueble {category.lower()} serie {serie}",
                    'zone_prices': product['zone_prices'],
                    'imported_at': datetime.utcnow().isoformat(),
                    'source': 'tarifa_tecnica_2025'
                })
    
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
    
    client.close()
    return len(products_to_import)

if __name__ == '__main__':
    asyncio.run(import_products())
