# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Script de extracción de datos del catálogo MV (Muebles Valencia)
Extrae productos de PDFs escaneados usando OCR
Sistema de TARIFAS (T1-T21) en lugar de ZONAS
"""
import re
import os
import json
from datetime import datetime, timezone
from pdf2image import convert_from_path
import pytesseract
import pymongo

# Conexión MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['test_database']

def extract_tariff_data(pdf_path, start_tariff=1):
    """
    Extrae datos de productos del catálogo MV desde un PDF escaneado.
    Retorna un diccionario con productos organizados por tarifa.
    """
    print(f"Procesando: {pdf_path}")
    
    # Convertir PDF a imágenes
    images = convert_from_path(pdf_path, dpi=150)
    print(f"Total páginas: {len(images)}")
    
    products = []
    current_tariff = start_tariff
    current_category = ""
    
    for page_num, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang='spa')
        lines = text.split('\n')
        
        # Detectar cambio de tarifa
        tariff_match = re.search(r'TARIFA\s*(\d+)', text, re.IGNORECASE)
        if tariff_match:
            current_tariff = int(tariff_match.group(1))
        
        # Detectar categoría
        category_patterns = [
            (r'\bPUERTAS?\b', 'PUERTA'),
            (r'\bVITRINA\s*INGLESA\b', 'VITRINA_INGLESA'),
            (r'\bVITRINA\b', 'VITRINA'),
            (r'\bREJILLA\b', 'REJILLA'),
            (r'\bBAJO\s*FREGADERO\b', 'BAJO_FREGADERO'),
            (r'\bBAJO\s*RINCON\b', 'BAJO_RINCON'),
            (r'\bBAJO\s*TERMINAL\b', 'BAJO_TERMINAL'),
            (r'\bBAJO\s*\d*\s*CAJON', 'BAJO_CAJONES'),
            (r'\bBAJO\s*\d*\s*GAVETA', 'BAJO_GAVETAS'),
            (r'\bBAJO\s*PUERTA', 'BAJO_PUERTA'),
            (r'\bBAJO\b', 'BAJO'),
            (r'\bALTO\s*VITRINA\b', 'ALTO_VITRINA'),
            (r'\bALTO\s*CAMPANA\b', 'ALTO_CAMPANA'),
            (r'\bALTO\s*ESCURREPLATOS\b', 'ALTO_ESCURREPLATOS'),
            (r'\bALTO\s*MICROONDAS\b', 'ALTO_MICROONDAS'),
            (r'\bALTO\s*RINCON\b', 'ALTO_RINCON'),
            (r'\bALTO\s*CALENTADOR\b', 'ALTO_CALENTADOR'),
            (r'\bALTO\s*CALDERA\b', 'ALTO_CALDERA'),
            (r'\bALTO\s*ABATIBLE\b', 'ALTO_ABATIBLE'),
            (r'\bALTO\s*COMBINADO\b', 'ALTO_COMBINADO'),
            (r'\bALTO\s*DECORATIVO\b', 'ALTO_DECORATIVO'),
            (r'\bALTO\b', 'ALTO'),
            (r'\bALTILLO\s*VITRINA\b', 'ALTILLO_VITRINA'),
            (r'\bALTILLO\b', 'ALTILLO'),
            (r'\bSOBREENC\w*\s*VIT\w*\s*CAJON\b', 'SOBREENC_VIT_CAJON'),
            (r'\bSOBREENC\w*\s*VITRINA\b', 'SOBREENC_VITRINA'),
            (r'\bSOBREENC\w*\s*CAJON\b', 'SOBREENC_CAJON'),
            (r'\bSOBREENCIMERA\b', 'SOBREENCIMERA'),
            (r'\bCOLUMNA\s*HORNO\s*MICRO\b', 'COLUMNA_HORNO_MICRO'),
            (r'\bCOLUMNA\s*HORNO\b', 'COLUMNA_HORNO'),
            (r'\bCOLUMNA\s*FRIGO\b', 'COLUMNA_FRIGO'),
            (r'\bCOLUMNA\s*DESPENSERO\b', 'COLUMNA_DESPENSERO'),
            (r'\bCOLUMNA\b', 'COLUMNA'),
            (r'\bMEDIACOLUMNA\s*VITRINA\b', 'MEDIACOLUMNA_VITRINA'),
            (r'\bMEDIACOLUMNA\s*HORNO\b', 'MEDIACOLUMNA_HORNO'),
            (r'\bMEDIACOLUMNA\b', 'MEDIACOLUMNA'),
            (r'\bBOTELLERO\b', 'BOTELLERO'),
            (r'\bCOSTADO\b', 'COSTADO'),
            (r'\bLATERAL\b', 'LATERAL'),
            (r'\bREGLETA\b', 'REGLETA'),
        ]
        
        for pattern, cat in category_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                current_category = cat
                break
        
        # Extraer códigos de producto y precios
        # Patrones de códigos MV
        code_patterns = [
            # Puertas: P25, P30, etc.
            r'\b(P\d{2,3})\b',
            # Vitrina: PV30, PVI30
            r'\b(PV[I]?\d{2,3})\b',
            # Rejilla: PR30
            r'\b(PR\d{2,3})\b',
            # Bajo: B25D/I, BF60, BC30, BCG30, etc.
            r'\b(B[A-Z]*\d{2,3}[D]?/?[IAL]?\*?)\b',
            # Alto: A25D/I*, AV30D/I*, etc.
            r'\b(A[A-Z]*\d{2,3}[D]?/?[IAL]?\*?)\b',
            # Columna: CH60D/I*, CD30D/I*, etc.
            r'\b(C[A-Z]*\d{2,3}[D]?/?[IAL]?\*?)\b',
            # Mediacolumna: M30D/I, MV30D/I, etc.
            r'\b(M[A-Z]*\d{2,3}[D]?/?[IAL]?\*?)\b',
            # Sobreencimera: S30D/I*, SC30D/I*, SV30D/I*, etc.
            r'\b(S[A-Z]*\d{2,3}[D]?/?[IAL]?\*?)\b',
            # Altillo: L30*, LV30*, LD30*
            r'\b(L[A-Z]*\d{2,3}\*?)\b',
        ]
        
        for line in lines:
            # Buscar líneas con códigos y números (precios)
            if re.search(r'\d{2,}', line):  # Tiene números de 2+ dígitos
                for pattern in code_patterns:
                    codes = re.findall(pattern, line, re.IGNORECASE)
                    for code in codes:
                        code = code.upper().strip()
                        if len(code) >= 3:
                            # Intentar extraer precio asociado
                            # Buscar números después del código
                            price_match = re.search(rf'{re.escape(code)}\s*(\d+)', line, re.IGNORECASE)
                            price = float(price_match.group(1)) if price_match else 0
                            
                            product = {
                                'code': code,
                                'name': f"{current_category} {code}",
                                'category': current_category,
                                'tariff': current_tariff,
                                'price': price,
                                'page': page_num + 1,
                                'library': 'MV'
                            }
                            products.append(product)
        
        if (page_num + 1) % 10 == 0:
            print(f"  Procesadas {page_num + 1} páginas...")
    
    return products


def consolidate_products(raw_products):
    """
    Consolida productos duplicados y organiza precios por tarifa.
    """
    product_map = {}
    
    for p in raw_products:
        code = p['code']
        tariff = p['tariff']
        
        if code not in product_map:
            product_map[code] = {
                'code': code,
                'name': p['name'],
                'category': p['category'],
                'library': 'MV',
                'manufacturer': 'MV',
                'tariffPrices': {},  # T1, T2, ... T21
                'module': 'montada'
            }
        
        # Añadir precio para esta tarifa
        tariff_key = f"T{tariff}"
        if p['price'] > 0:
            product_map[code]['tariffPrices'][tariff_key] = p['price']
    
    return list(product_map.values())


def save_to_mongodb(products):
    """
    Guarda productos en MongoDB.
    """
    created = 0
    updated = 0
    
    for prod in products:
        code = prod['code']
        
        # Buscar producto existente en biblioteca MV
        existing = db.products.find_one({'code': code, 'library': 'MV'})
        
        product_data = {
            'id': existing.get('id') if existing else f"prod-mv-{code.lower().replace('/', '-')}",
            'code': code,
            'name': prod['name'],
            'category': prod['category'],
            'library': 'MV',
            'manufacturer': 'MV',
            'module': 'montada',
            'tariffPrices': prod.get('tariffPrices', {}),
            # Precio por defecto es T1
            'points': prod.get('tariffPrices', {}).get('T1', 0),
            'createdAt': existing.get('createdAt') if existing else datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            db.products.update_one({'code': code, 'library': 'MV'}, {'$set': product_data})
            updated += 1
        else:
            db.products.insert_one(product_data)
            created += 1
    
    return created, updated


if __name__ == '__main__':
    # Procesar PDF del catálogo MV
    pdf_path = '/app/MV_catalogo_1_90.pdf'
    
    if os.path.exists(pdf_path):
        print("="*60)
        print("EXTRACCIÓN CATÁLOGO MV (Muebles Valencia)")
        print("="*60)
        
        # Extraer datos
        raw_products = extract_tariff_data(pdf_path)
        print(f"\nProductos brutos extraídos: {len(raw_products)}")
        
        # Consolidar
        products = consolidate_products(raw_products)
        print(f"Productos únicos consolidados: {len(products)}")
        
        # Mostrar muestra
        print("\n=== MUESTRA DE PRODUCTOS ===")
        for p in products[:20]:
            print(f"  {p['code']}: {p['name']} - Tarifas: {list(p['tariffPrices'].keys())}")
        
        # Guardar en MongoDB
        print("\n=== GUARDANDO EN MONGODB ===")
        created, updated = save_to_mongodb(products)
        print(f"Creados: {created}, Actualizados: {updated}")
        
        # Actualizar biblioteca MV
        db.libraries.update_one(
            {'code': 'MV'},
            {'$set': {
                'isActive': True,
                'productCount': db.products.count_documents({'library': 'MV'}),
                'pricingSystem': 'tariffs',
                'priceLevels': [f"T{i}" for i in range(1, 22)]  # T1-T21
            }},
            upsert=True
        )
        print("\nBiblioteca MV actualizada.")
        
    else:
        print(f"ERROR: No se encontró el archivo {pdf_path}")
