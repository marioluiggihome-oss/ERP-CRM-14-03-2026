#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Script de migración para corregir dimensiones de productos MV.

REGLAS:
- ALTOS: fondo = 33cm, ancho parseado del código, variantes H70/H90 con precios distintos
- BAJOS: fondo = 58cm, ancho parseado del código, variantes H70/H80 con mismo precio
- BAJO FREGADERO: crear variantes con/sin chapa aluminio
"""
import os
import re
from pymongo import MongoClient
from datetime import datetime, timezone

def parse_width_from_code(code):
    """Extrae el ancho del código del producto."""
    if not code:
        return None
    
    # Patrones comunes: A25, A30, B25, B30, BF45, etc.
    # El número después de la letra inicial es el ancho
    patterns = [
        r'^[A-Z]+(\d+)',  # BF45, A25, B30, etc.
    ]
    
    for pattern in patterns:
        match = re.search(pattern, code.upper())
        if match:
            width = int(match.group(1))
            # Algunos códigos tienen D/I al final que no son parte del ancho
            return width
    
    return None

def main():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'luiggi_home')
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    now = datetime.now(timezone.utc)
    
    print("=" * 60)
    print("MIGRACIÓN DE PRODUCTOS MV - CORRECCIÓN DE DIMENSIONES")
    print("=" * 60)
    
    # ========================================
    # 1. CORREGIR ALTOS (fondo = 33cm)
    # ========================================
    print("\n[1/4] CORRIGIENDO ALTOS (fondo = 33cm)...")
    
    alto_categories = [
        'ALTOS', 'ALTO ABATIBLE', 'ALTO CALDERA', 'ALTO CALENTADOR', 
        'ALTO CAMPANA', 'ALTO COMBINADO PLUS', 'ALTO DECORATIVO',
        'ALTO ESCURREPLATOS', 'ALTO MICROONDAS', 'ALTO RINCON CHAFLAN',
        'ALTO RINCON CIEGO', 'ALTO RINCON ESCUADRA', 'ALTO SOBREFRIGO',
        'ALTO TERMINAL', 'ALTO VITRINA', 'ALTILLO', 'ALTILLO VITRINA',
        'ALTILLOS DECORATIVOS'
    ]
    
    altos_updated = 0
    for cat in alto_categories:
        products = list(db.products.find({'library': 'MV', 'category': cat}))
        for p in products:
            code = p.get('code', '')
            width = parse_width_from_code(code)
            
            update = {'depth': 33, 'updatedAt': now}
            if width:
                update['width'] = float(width)
            
            db.products.update_one({'_id': p['_id']}, {'$set': update})
            altos_updated += 1
    
    print(f"   ✓ Actualizados {altos_updated} productos ALTOS (fondo=33cm)")
    
    # ========================================
    # 2. CORREGIR BAJOS (fondo = 58cm)
    # ========================================
    print("\n[2/4] CORRIGIENDO BAJOS (fondo = 58cm)...")
    
    bajo_categories = [
        'BAJOS', 'BAJO FREGADERO', 'BAJO HORNO', 'BAJO PUERTA Y CAJON',
        'BAJO RINCON CIEGO', 'BAJO RINCON ESCUADRA', 'BAJO TERMINAL',
        'BAJO 2 CAJONES', 'BAJO 2 GAVETAS+1 CAJON', 'BAJO 2 GAVETAS+1 FRENTE',
        'BAJO 3 CAJONES+1 GAVETA'
    ]
    
    bajos_updated = 0
    for cat in bajo_categories:
        products = list(db.products.find({'library': 'MV', 'category': cat}))
        for p in products:
            code = p.get('code', '')
            width = parse_width_from_code(code)
            
            update = {'depth': 58, 'updatedAt': now}
            if width:
                update['width'] = float(width)
            
            db.products.update_one({'_id': p['_id']}, {'$set': update})
            bajos_updated += 1
    
    print(f"   ✓ Actualizados {bajos_updated} productos BAJOS (fondo=58cm)")
    
    # ========================================
    # 3. CREAR VARIANTES H70/H80 PARA BAJOS
    # ========================================
    print("\n[3/4] CREANDO VARIANTES H70/H80 PARA BAJOS...")
    
    # Para los BAJOS que no tienen variantes de altura, crear ambas H70 y H80
    # El precio es el mismo para ambas alturas
    
    variants_created = 0
    
    for cat in bajo_categories:
        products = list(db.products.find({'library': 'MV', 'category': cat, 'height': {'$in': [0, None]}}))
        
        for p in products:
            # Obtener precio base
            base_price = p.get('points', 0)
            base_code = p.get('code', '')
            base_name = p.get('name', '')
            
            # Crear variante H70
            h70_product = p.copy()
            del h70_product['_id']
            h70_product['id'] = f"{p.get('id')}-H70"
            h70_product['height'] = 70
            h70_product['name'] = f"{base_name} H70"
            h70_product['updatedAt'] = now
            
            # Crear variante H80
            h80_product = p.copy()
            del h80_product['_id']
            h80_product['id'] = f"{p.get('id')}-H80"
            h80_product['height'] = 80
            h80_product['name'] = f"{base_name} H80"
            h80_product['updatedAt'] = now
            
            # Verificar si ya existen
            existing_h70 = db.products.find_one({'library': 'MV', 'code': base_code, 'height': 70})
            existing_h80 = db.products.find_one({'library': 'MV', 'code': base_code, 'height': 80})
            
            if not existing_h70:
                db.products.insert_one(h70_product)
                variants_created += 1
            
            if not existing_h80:
                db.products.insert_one(h80_product)
                variants_created += 1
            
            # Actualizar el producto original para que tenga H70 por defecto si no tiene altura
            if p.get('height', 0) == 0:
                db.products.update_one({'_id': p['_id']}, {'$set': {'height': 70}})
    
    print(f"   ✓ Creadas {variants_created} variantes H70/H80 para BAJOS")
    
    # ========================================
    # 4. CREAR VARIANTES CHAPA ALUMINIO PARA BAJO FREGADERO
    # ========================================
    print("\n[4/4] CREANDO VARIANTES CON CHAPA PARA BAJO FREGADERO...")
    
    # Buscar precios de chapa en la tarifa (según user, hay una columna "chapa")
    # Por ahora, crear las variantes con el nombre indicativo
    
    fregaderos = list(db.products.find({'library': 'MV', 'category': 'BAJO FREGADERO'}))
    chapa_variants_created = 0
    
    for p in fregaderos:
        base_name = p.get('name', '')
        base_code = p.get('code', '')
        base_price = p.get('points', 0)
        
        # Si ya tiene "CHAPA" en el nombre, es una variante existente
        if 'CHAPA' in base_name.upper():
            continue
        
        # Verificar si ya existe la variante con chapa
        existing_chapa = db.products.find_one({
            'library': 'MV', 
            'code': base_code,
            'name': {'$regex': 'CHAPA', '$options': 'i'}
        })
        
        if not existing_chapa:
            # Crear variante con chapa aluminio
            chapa_product = p.copy()
            del chapa_product['_id']
            chapa_product['id'] = f"{p.get('id')}-CHAPA"
            chapa_product['name'] = f"{base_name} CON CHAPA ALUMINIO"
            chapa_product['hasAluminumSheet'] = True
            chapa_product['updatedAt'] = now
            # El precio con chapa se debe obtener de la tarifa
            # Por ahora marcamos que necesita el precio de chapa
            chapa_product['needsChapaPrice'] = True
            
            db.products.insert_one(chapa_product)
            chapa_variants_created += 1
    
    print(f"   ✓ Creadas {chapa_variants_created} variantes CON CHAPA para BAJO FREGADERO")
    print(f"   ⚠ NOTA: Los precios de CHAPA necesitan ser actualizados desde la tarifa")
    
    # ========================================
    # RESUMEN
    # ========================================
    print("\n" + "=" * 60)
    print("RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    
    total_mv = db.products.count_documents({'library': 'MV'})
    print(f"\n✓ Total productos MV después de migración: {total_mv}")
    
    # Verificar algunas muestras
    print("\n--- VERIFICACIÓN DE MUESTRAS ---")
    
    # Muestra ALTO
    alto_sample = db.products.find_one({'library': 'MV', 'category': 'ALTOS', 'code': 'A100'})
    if alto_sample:
        print(f"\nALTO A100: W={alto_sample.get('width')}cm, D={alto_sample.get('depth')}cm, H={alto_sample.get('height')}cm")
    
    # Muestra BAJO
    bajo_sample = db.products.find_one({'library': 'MV', 'category': 'BAJOS', 'code': {'$regex': '^B25'}})
    if bajo_sample:
        print(f"BAJO B25: W={bajo_sample.get('width')}cm, D={bajo_sample.get('depth')}cm, H={bajo_sample.get('height')}cm")
    
    # Muestra BAJO FREGADERO
    bf_sample = db.products.find_one({'library': 'MV', 'category': 'BAJO FREGADERO', 'hasAluminumSheet': True})
    if bf_sample:
        print(f"BAJO FREGADERO CHAPA: {bf_sample.get('name')}")
    
    print("\n✓ Migración completada!")

if __name__ == "__main__":
    main()
