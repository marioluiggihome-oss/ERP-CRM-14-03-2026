"""
Extractor de precios de la tarifa MV desde imágenes JPG
Procesa todas las imágenes y extrae códigos de producto con sus precios por tarifa
"""
import os
import re
from PIL import Image
import pytesseract
import pymongo
from datetime import datetime, timezone

# Conexión MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['test_database']

def extract_tariff_from_image(image_path):
    """Extrae información de tarifa desde una imagen"""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='spa')
    
    # Detectar número de tarifa
    tariff_match = re.search(r'TARIFA\s*(\d+)', text, re.IGNORECASE)
    tariff_num = int(tariff_match.group(1)) if tariff_match else None
    
    return text, tariff_num

def parse_product_prices(text, tariff_num):
    """
    Parsea el texto OCR y extrae productos con precios.
    Retorna lista de {code, category, prices}
    """
    products = []
    lines = text.split('\n')
    
    current_category = ""
    
    # Patrones de categorías
    category_keywords = [
        'PUERTA', 'VITRINA', 'REJILLA', 'BAJO', 'ALTO', 'COLUMNA', 
        'MEDIA', 'ALTILLO', 'SOBRE', 'COSTADO', 'REGLETA', 'BOTELLERO',
        'FREGADERO', 'RINCON', 'HORNO', 'MICRO', 'CAMPANA', 'ESCURRE',
        'CALENTADOR', 'ABATIBLE', 'COMBINADO', 'TERMINAL', 'FRIGO'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detectar categoría
        for keyword in category_keywords:
            if keyword in line.upper():
                current_category = line.upper()[:50]
                break
        
        # Buscar códigos de producto MV
        # Patrones: B30D/I, A45*, CH60D/I*, etc.
        code_patterns = [
            r'\b([ABCMLPS][A-Z]*\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(BF\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(BPC\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(BCG?\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(AV\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(CH[MCG]*\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(MV?G?\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(SV?C?\d{2,3}[D]?/?[IA]?\*?)\b',
            r'\b(L[VD]?\d{2,3}\*?)\b',
            r'\b(P[VRI]?\d{2,3})\b',
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for code in matches:
                code = code.upper().strip()
                if len(code) >= 3:
                    # Extraer números que podrían ser precios
                    # Buscar todos los números en la línea
                    numbers = re.findall(r'\b(\d{2,4})\b', line)
                    
                    # Filtrar números razonables como precios (10-999)
                    prices = [int(n) for n in numbers if 10 <= int(n) <= 999]
                    
                    if prices:
                        products.append({
                            'code': code,
                            'category': current_category,
                            'tariff': tariff_num,
                            'prices': prices
                        })
    
    return products

def process_all_images(images_dir):
    """Procesa todas las imágenes del directorio"""
    all_products = {}
    
    images = sorted([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
    total = len(images)
    
    print(f"Procesando {total} imágenes...")
    
    for idx, img_name in enumerate(images):
        img_path = os.path.join(images_dir, img_name)
        
        try:
            text, tariff_num = extract_tariff_from_image(img_path)
            
            if tariff_num:
                products = parse_product_prices(text, tariff_num)
                
                for prod in products:
                    code = prod['code']
                    if code not in all_products:
                        all_products[code] = {
                            'code': code,
                            'category': prod['category'],
                            'tariffPrices': {}
                        }
                    
                    # Guardar el primer precio encontrado para esta tarifa
                    tariff_key = f"T{tariff_num}"
                    if tariff_key not in all_products[code]['tariffPrices'] and prod['prices']:
                        all_products[code]['tariffPrices'][tariff_key] = prod['prices'][0]
            
            if (idx + 1) % 20 == 0:
                print(f"  {idx + 1}/{total} imágenes procesadas...")
                
        except Exception as e:
            print(f"  Error en {img_name}: {e}")
    
    return all_products

def save_to_mongodb(products_dict):
    """Guarda los productos extraídos en MongoDB"""
    created = 0
    updated = 0
    
    for code, prod in products_dict.items():
        # Buscar producto existente
        existing = db.products.find_one({'code': code, 'library': 'MV'})
        
        if existing:
            # Merge tariffPrices
            old_prices = existing.get('tariffPrices', {})
            new_prices = {**old_prices, **prod['tariffPrices']}
            
            db.products.update_one(
                {'code': code, 'library': 'MV'},
                {'$set': {
                    'tariffPrices': new_prices,
                    'category': prod['category'] or existing.get('category', ''),
                    'points': new_prices.get('T1', 0) or list(new_prices.values())[0] if new_prices else 0
                }}
            )
            updated += 1
        else:
            # Crear nuevo
            product_data = {
                'id': f"prod-mv-{code.lower().replace('/', '-').replace('*', '')}",
                'code': code,
                'name': f"{prod['category']} {code}" if prod['category'] else code,
                'category': prod['category'] or 'SIN_CATEGORIA',
                'library': 'MV',
                'manufacturer': 'MV',
                'module': 'montada',
                'tariffPrices': prod['tariffPrices'],
                'points': prod['tariffPrices'].get('T1', 0) or (list(prod['tariffPrices'].values())[0] if prod['tariffPrices'] else 0),
                'createdAt': datetime.now(timezone.utc).isoformat()
            }
            db.products.insert_one(product_data)
            created += 1
    
    return created, updated

if __name__ == '__main__':
    images_dir = "/app/MV_images/Tarifa MV"
    
    print("="*60)
    print("EXTRACCIÓN TARIFA MV DESDE IMÁGENES JPG")
    print("="*60)
    
    # Procesar imágenes
    products = process_all_images(images_dir)
    
    print(f"\nProductos únicos extraídos: {len(products)}")
    print(f"Productos con precios: {sum(1 for p in products.values() if p['tariffPrices'])}")
    
    # Mostrar muestra
    print("\n=== MUESTRA DE PRODUCTOS ===")
    count = 0
    for code, prod in products.items():
        if prod['tariffPrices']:
            print(f"  {code}: {prod['category'][:30]} - Precios: {prod['tariffPrices']}")
            count += 1
            if count >= 20:
                break
    
    # Guardar en MongoDB
    print("\n=== GUARDANDO EN MONGODB ===")
    created, updated = save_to_mongodb(products)
    print(f"Creados: {created}, Actualizados: {updated}")
    
    # Actualizar biblioteca
    total_mv = db.products.count_documents({'library': 'MV'})
    with_prices = db.products.count_documents({'library': 'MV', 'tariffPrices': {'$ne': {}}})
    
    db.libraries.update_one(
        {'code': 'MV'},
        {'$set': {'productCount': total_mv, 'isActive': True}}
    )
    
    print(f"\nTotal productos MV: {total_mv}")
    print(f"Productos con precios: {with_prices}")
