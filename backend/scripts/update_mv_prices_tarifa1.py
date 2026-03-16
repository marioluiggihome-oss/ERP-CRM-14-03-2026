#!/usr/bin/env python3
"""
Script para actualizar TODOS los precios de productos MV según TARIFA 1
Basado en extracción manual de las 5 páginas de tarifa proporcionadas por el usuario
"""
from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient('mongodb://localhost:27017')
db = client['luiggi_home']

# ============================================================================
# PÁGINA 1: PUERTAS, VITRINA, REJILLA CONFESIONARIO
# ============================================================================

# PUERTAS (P25-P60) - Precios por altura
PUERTAS_PRICES = {
    # Format: (code_base, height): price
    ('P25', 14): 4, ('P30', 14): 4, ('P35', 14): 4, ('P40', 14): 4, ('P45', 14): 4, ('P50', 14): 4, ('P60', 14): 4,
    ('P25', 28): 5, ('P30', 28): 5, ('P35', 28): 6, ('P40', 28): 6, ('P45', 28): 7, ('P50', 28): 7, ('P60', 28): 8,
    ('P25', 40): 9, ('P30', 40): 9, ('P35', 40): 10, ('P40', 40): 10, ('P45', 40): 10, ('P50', 40): 11, ('P60', 40): 11,
    ('P25', 56): 10, ('P30', 56): 10, ('P35', 56): 11, ('P40', 56): 11, ('P45', 56): 11, ('P50', 56): 13, ('P60', 56): 13,
    ('P25', 70): 10, ('P30', 70): 11, ('P35', 70): 12, ('P40', 70): 13, ('P45', 70): 13, ('P50', 70): 14, ('P60', 70): 16,
    ('P25', 90): 13, ('P30', 90): 14, ('P35', 90): 15, ('P40', 90): 15, ('P45', 90): 16, ('P50', 90): 17, ('P60', 90): 19,
    ('P25', 127): 16, ('P30', 127): 17, ('P35', 127): 19, ('P40', 127): 19, ('P45', 127): 19, ('P50', 127): 20, ('P60', 127): 22,
    ('P25', 147): 19, ('P30', 147): 19, ('P35', 147): 20, ('P40', 147): 21, ('P45', 147): 22, ('P50', 147): 23, ('P60', 147): 26,
}

# VITRINA (PV30-PV60) - Precios por altura
VITRINA_PRICES = {
    ('PV30', 28): 20, ('PV35', 28): 22, ('PV40', 28): 23, ('PV45', 28): 24, ('PV50', 28): 25, ('PV60', 28): 28,
    ('PV30', 40): 34, ('PV35', 40): 36, ('PV40', 40): 37, ('PV45', 40): 38, ('PV50', 40): 40, ('PV60', 40): 42,
    ('PV30', 70): 40, ('PV35', 70): 43, ('PV40', 70): 45, ('PV45', 70): 47, ('PV50', 70): 49, ('PV60', 70): 54,
    ('PV30', 90): 49, ('PV35', 90): 52, ('PV40', 90): 54, ('PV45', 90): 57, ('PV50', 90): 59, ('PV60', 90): 65,
    ('PV30', 127): 68, ('PV35', 127): 72, ('PV40', 127): 76, ('PV45', 127): 81, ('PV50', 127): 85, ('PV60', 127): 89,
    ('PV30', 147): 77, ('PV35', 147): 82, ('PV40', 147): 87, ('PV45', 147): 92, ('PV50', 147): 97, ('PV60', 147): 118,
}

# REJILLA CONFESIONARIO (PR30-PR60)
REJILLA_PRICES = {
    ('PR30', 70): 41, ('PR35', 70): 45, ('PR40', 70): 48, ('PR45', 70): 51, ('PR50', 70): 56, ('PR60', 70): 63,
    ('PR30', 90): 51, ('PR35', 90): 55, ('PR40', 90): 60, ('PR45', 90): 65, ('PR50', 90): 68, ('PR60', 90): 78,
    ('PR30', 127): 55, ('PR35', 127): 60, ('PR40', 127): 67, ('PR45', 127): 71, ('PR50', 127): 78, ('PR60', 127): 89,
    ('PR30', 147): 63, ('PR35', 147): 69, ('PR40', 147): 76, ('PR45', 147): 82, ('PR50', 147): 88, ('PR60', 147): 109,
}

# ============================================================================
# PÁGINA 2: BAJOS
# ============================================================================

# BAJO básico (confirmado por usuario: B25=40, B30=41)
BAJO_PRICES = {
    'B25': 40, 'B30': 41, 'B35': 42, 'B40': 46, 'B45': 48,
    'B50': 52, 'B60': 54, 'B70': 56, 'B80': 57, 'B90': 59, 'B100': 68,
}

# BAJO FREGADERO
BAJO_FREGADERO_PRICES = {
    'BF45': 41, 'BF50': 47, 'BF60': 52, 'BF70': 54, 'BF80': 56,
    'BF90': 57, 'BF100': 59, 'BF120': 68,
}

# BAJO FREGADERO con chapa (columna chapa)
BAJO_FREGADERO_CHAPA_PRICES = {
    'BF45': 47, 'BF50': 48, 'BF60': 59, 'BF70': 60, 'BF80': 60,
    'BF90': 64, 'BF100': 67, 'BF120': 81,
}

# BAJO RINCON ESCUADRA
BAJO_RINCON_ESCUADRA_PRICES = {
    'BRI95': 87, 'BRU95': 88,
}

# BAJO RINCON CIEGO
BAJO_RINCON_CIEGO_PRICES = {
    'BR90': 81, 'BR95': 87, 'BR100': 87, 'BR105': 87, 'BR110': 87,
}

# BAJO HORNO
BAJO_HORNO_PRICES = {
    'BH60': 37, 'BHC60': 45, 'BHZ60': 77, 'BHG60': 80,
}

# BAJO TERMINAL
BAJO_TERMINAL_PRICES = {
    'BT30': 58, 'BTS30': 63, 'BTZ30': 72, 'BTP33': 65,
}

# BAJO 2 GAVETAS+1FRENTE
BGF_PRICES = {
    'BGF60': 97, 'BGF70': 120, 'BGF80': 123, 'BGF90': 125, 'BGF120': 153,
}

# BAJO 2 CAJONES+1GB
BCG_PRICES = {
    'BCG30': 112, 'BCG35': 114, 'BCG40': 116, 'BCG45': 118,
    'BCG50': 120, 'BCG60': 124, 'BCG70': 126, 'BCG80': 130, 'BCG90': 134,
}

# BAJO 3 CAJONES+1GA
BCGC_PRICES = {
    'BCGC30': 140, 'BCGC40': 144, 'BCGC45': 146, 'BCGC50': 150,
    'BCGC60': 155, 'BCGC70': 142, 'BCGC80': 147, 'BCGC90': 154,
}

# BAJO PUERTA Y CAJON
BPC_PRICES = {
    'BPC30': 72, 'BPC35': 74, 'BPC40': 76, 'BPC45': 82,
    'BPC50': 82, 'BPC60': 126, 'BPC70': 130, 'BPC80': 133, 'BPC90': 134, 'BPC100': 138,
}

# BAJO 5 CAJONES
BC5_PRICES = {
    'BC35': 168, 'BC40': 171, 'BC45': 173, 'BC50': 176,
    'BC60': 179, 'BC70': 184, 'BC80': 199, 'BC90': 203, 'BC100': 208,
}

# ============================================================================
# PÁGINA 3: ALTOS (con H70 y H90)
# ============================================================================

# ALTO básico
ALTO_PRICES = {
    ('A25', 70): 38, ('A25', 90): 42,
    ('A30', 70): 39, ('A30', 90): 43,
    ('A35', 70): 40, ('A35', 90): 44,
    ('A40', 70): 41, ('A40', 90): 45,
    ('A45', 70): 42, ('A45', 90): 46,
    ('A50', 70): 44, ('A50', 90): 48,
    ('A60', 70): 46, ('A60', 90): 52,
    ('A70', 70): 48, ('A70', 90): 53,
    ('A80', 70): 52, ('A80', 90): 58,
    ('A90', 70): 55, ('A90', 90): 62,
    ('A100', 70): 62, ('A100', 90): 70,
}

# ALTO CAMPANA
ALTO_CAMPANA_PRICES = {
    ('ASC60', 70): 70, ('ASC60', 90): 90,
    ('ASC90', 70): 40, ('ASC90', 90): 46,
    ('ASCE60', 70): 53, ('ASCE60', 90): 62,
}

# ALTO RINCON CIEGO
ALTO_RINCON_CIEGO_PRICES = {
    ('AR60', 70): 54, ('AR60', 90): 60,
    ('AR65', 70): 70, ('AR65', 90): 67,
}

# ALTO RINCON ESCUADRA
ALTO_RINCON_ESCUADRA_PRICES = {
    ('ARI65', 70): 82, ('ARI65', 90): 89,
    ('ARU65', 70): 84, ('ARU65', 90): 90,
}

# ALTO RINCON CHAFLAN
ALTO_RINCON_CHAFLAN_PRICES = {
    ('ARC63', 70): 70, ('ARC63', 90): 84,
    ('ARCV83', 70): 84, ('ARCV83', 90): 95,
}

# ALTO DECORATIVO
ALTO_DECORATIVO_PRICES = {
    ('AD40', 70): 36, ('AD40', 90): 43,
    ('AD45', 70): 37, ('AD45', 90): 44,
    ('AD50', 70): 39, ('AD50', 90): 47,
    ('AD60', 70): 42, ('AD60', 90): 51,
    ('AD70', 70): 46, ('AD70', 90): 56,
    ('AD80', 70): 48, ('AD80', 90): 59,
    ('AD90', 70): 51, ('AD90', 90): 64,
    ('AD100', 70): 55, ('AD100', 90): 68,
}

# ALTO TERMINAL
ALTO_TERMINAL_PRICES = {
    ('AT30', 70): 52, ('AT30', 90): 64,
    ('ATP33', 70): 63, ('ATP33', 90): 71,
}

# ALTO SOBREFRIGO
ALTO_SOBREFRIGO_PRICES = {
    ('ASF60', 70): 39, ('ASF60', 90): 46,
    ('ASF60A', 70): 46, ('ASF60A', 90): 51,
    ('ASF60P', 70): 49, ('ASF60P', 90): 55,
}

# ALTO CALDERA
ALTO_CALDERA_PRICES = {
    ('ACC60', 70): 49, ('ACC60', 90): 51,
    ('ACC60A', 70): 56, ('ACC60A', 90): 62,
}

# ALTO CALENTADOR
ALTO_CALENTADOR_PRICES = {
    ('ACA45', 70): 36, ('ACA45', 90): 40,
    ('ACA60', 70): 37, ('ACA60', 90): 41,
}

# ALTO MICROONDAS
ALTO_MICROONDAS_PRICES = {
    ('AM60', 70): 40, ('AM60', 90): 47,
    ('AMF60', 70): 47, ('AMF60', 90): 52,
}

# ALTO ESCURREPLATOS
ALTO_ESCURREPLATOS_PRICES = {
    ('AE45', 70): 53, ('AE45', 90): 61,
    ('AE50', 70): 53, ('AE50', 90): 67,
    ('AE60', 70): 61, ('AE60', 90): 73,
    ('AE70', 70): 65, ('AE70', 90): 76,
    ('AE80', 70): 77, ('AE80', 90): 88,
    ('AE90', 70): 80, ('AE90', 90): 90,
    ('AE100', 70): 88, ('AE100', 90): 98,
}

# ALTO VITRINA
ALTO_VITRINA_PRICES = {
    ('AV30', 70): 68, ('AV30', 90): 77,
    ('AV35', 70): 72, ('AV35', 90): 82,
    ('AV40', 70): 78, ('AV40', 90): 86,
    ('AV45', 70): 86, ('AV45', 90): 96,
    ('AV50', 70): 110, ('AV50', 90): 116,
    ('AV60', 70): 116, ('AV60', 90): 125,
    ('AV70', 70): 125, ('AV70', 90): 136,
    ('AV80', 70): 146, ('AV80', 90): 156,
    ('AV90', 70): 131, ('AV90', 90): 146,
    ('AV100', 70): 140, ('AV100', 90): 185,
}

# ============================================================================
# PÁGINA 4: MÁS ALTOS Y OTROS
# ============================================================================

# ALTO ABATIBLE
ALTO_ABATIBLE_PRICES = {
    ('AA45', 70): 70, ('AA45', 90): 95,
    ('AA60', 70): 95, ('AA60', 90): 99,
    ('AA70', 70): 106, ('AA70', 90): 110,
    ('AA80', 70): 109, ('AA80', 90): 118,
    ('AA90', 70): 121, ('AA90', 90): 121,
    ('AA100', 70): 115, ('AA100', 90): 123,
}

# ALTO COMBINADO PLUS
ALTO_COMBINADO_PLUS_PRICES = {
    ('ACP45', 70): 127, ('ACP45', 90): 139,
    ('ACP50', 70): 129, ('ACP50', 90): 142,
    ('ACP60', 70): 138, ('ACP60', 90): 154,
    ('ACP70', 70): 141, ('ACP70', 90): 156,
    ('ACP80', 70): 149, ('ACP80', 90): 165,
    ('ACP90', 70): 150, ('ACP90', 90): 162,
    ('ACP100', 70): 152, ('ACP100', 90): 169,
}

# ALTILLO
ALTILLO_PRICES = {
    ('L30', 70): 65, ('L30', 90): 70,
    ('L35', 70): 66, ('L35', 90): 69,
    ('L40', 70): 66, ('L40', 90): 71,
    ('L45', 70): 67, ('L45', 90): 72,
    ('L50', 70): 68, ('L50', 90): 73,
    ('L60', 70): 69, ('L60', 90): 75,
    ('L70', 70): 71, ('L70', 90): 80,
    ('L80', 70): 73, ('L80', 90): 82,
    ('L90', 70): 75, ('L90', 90): 84,
    ('L100', 70): 77, ('L100', 90): 86,
}

# SOBREENCIMERA
SOBREENCIMERA_PRICES = {
    ('S30', 127): 51, ('S30', 147): 54,
    ('S35', 127): 52, ('S35', 147): 56,
    ('S40', 127): 54, ('S40', 147): 58,
    ('S45', 127): 56, ('S45', 147): 59,
    ('S50', 127): 57, ('S50', 147): 62,
    ('S60', 127): 60, ('S60', 147): 65,
}

# SOBREENCIMERA CAJON
SOBREENCIMERA_CAJON_PRICES = {
    ('SC30', 127): 72, ('SC30', 147): 74,
    ('SC35', 127): 74, ('SC35', 147): 78,
    ('SC40', 127): 76, ('SC40', 147): 80,
    ('SC45', 127): 78, ('SC45', 147): 82,
    ('SC50', 127): 80, ('SC50', 147): 84,
    ('SC60', 127): 83, ('SC60', 147): 88,
}

# SOBREENCIMERA VITRINA
SOBREENCIMERA_VITRINA_PRICES = {
    ('SVC30', 127): 122, ('SVC30', 147): 132,
    ('SVC35', 127): 128, ('SVC35', 147): 138,
    ('SVC40', 127): 132, ('SVC40', 147): 143,
    ('SVC45', 127): 137, ('SVC45', 147): 149,
    ('SVC50', 127): 143, ('SVC50', 147): 155,
    ('SVC60', 127): 170, ('SVC60', 147): 185,
}

# ALTILLO VITRINA
ALTILLO_VITRINA_PRICES = {
    ('LV35', 70): 83, ('LV35', 90): 98,
    ('LV40', 70): 92, ('LV40', 90): 101,
    ('LV45', 70): 93, ('LV45', 90): 103,
    ('LV50', 70): 95, ('LV50', 90): 106,
    ('LV60', 70): 97, ('LV60', 90): 108,
    ('LV70', 70): 100, ('LV70', 90): 116,
    ('LV80', 70): 103, ('LV80', 90): 118,
    ('LV90', 70): 105, ('LV90', 90): 120,
    ('LV100', 70): 107, ('LV100', 90): 126,
}

# ============================================================================
# PÁGINA 5: COLUMNAS
# ============================================================================

# COLUMNA DESPENSERO
COLUMNA_DESPENSERO_PRICES = {
    ('CD30', 200): 90, ('CD30', 220): 91,
    ('CD35', 200): 91, ('CD35', 220): 94,
    ('CD40', 200): 96, ('CD40', 220): 101,
    ('CD45', 200): 99, ('CD45', 220): 103,
    ('CD50', 200): 102, ('CD50', 220): 112,
    ('CD60', 200): 125, ('CD60', 220): 132,
    ('CD70', 200): 145, ('CD70', 220): 152,
    ('CD80', 200): 163, ('CD80', 220): 170,
    ('CD90', 200): 181, ('CD90', 220): 191,
}

# COLUMNA FRIGO
COLUMNA_FRIGO_PRICES = {
    ('CF60', 200): 63, ('CF60', 220): 69,
    ('CFP60', 200): 75, ('CFP60', 220): 79,
}

# COLUMNA HORNO
COLUMNA_HORNO_PRICES = {
    ('CH60', 200): 110, ('CH60', 220): 117,
    ('CHPC60', 200): 129, ('CHPC60', 220): 134,
    ('CHC60', 200): 167, ('CHC60', 220): 173,
    ('CHGC60', 200): 143, ('CHGC60', 220): 151,
    ('CHMC60', 200): 234, ('CHMC60', 220): 237,
    ('CHM60', 200): 240, ('CHM60', 220): 246,
}

# MEDIACOLUMNA
MEDIACOLUMNA_PRICES = {
    ('M30', 130): 63, ('M35', 130): 65, ('M40', 130): 63, ('M45', 130): 65, ('M60', 130): 69,
}

# MEDIACOLUMNA VITRINA
MEDIACOLUMNA_VITRINA_PRICES = {
    ('MV30', 130): 162, ('MV35', 130): 167, ('MV40', 130): 197, ('MV45', 130): 205, ('MV60', 130): 210,
}

# MEDIA PUERTA GAVETA
MEDIA_PUERTA_GAVETA_PRICES = {
    ('MPG30', 130): 85, ('MPG35', 130): 87, ('MPG40', 130): 89, ('MPG45', 130): 92, ('MPG50', 130): 95, ('MPG60', 130): 79,
}

# MEDIACOLUMNA HORNO
MEDIACOLUMNA_HORNO_PRICES = {
    ('MPH60', 130): 130, ('MGHM60', 130): 105,
}

# BOTELLEROS
BOTELLERO_PRICES = {
    'BOA': 41, 'BOS': 47, 'BOC': 66, 'BOCA': 47, 'MCHM': 88,
}

# ALTILLOS DECORATIVOS
ALTILLOS_DECORATIVOS_PRICES = {
    'LD30': 23, 'LD35': 24, 'LD40': 25, 'LD45': 26, 'LD50': 27,
    'LD60': 29, 'LD70': 30, 'LD80': 33, 'LD90': 34, 'LD100': 36,
}

# MEDIACOLUMNA GAVETA
MEDIACOL_GAVETA_PRICES = {
    ('MVG30', 130): 130, ('MVG35', 130): 131, ('MVG40', 130): 135, ('MVG45', 130): 141, ('MVG50', 130): 146, ('MVG60', 130): 159,
}


def update_prices():
    """Update all MV product prices based on TARIFA 1"""
    updated = 0
    not_found = []
    
    # Helper function to update a product
    def update_product(code, price, series_filter=None, height_filter=None):
        nonlocal updated
        query = {'library': 'MV', 'code': code}
        if series_filter:
            query['series'] = series_filter
        if height_filter:
            query['height'] = height_filter
        
        result = db.products.update_many(
            query,
            {
                '$set': {
                    'points': float(price),
                    'zonePoints.T1': float(price),
                    'updatedAt': datetime.now(timezone.utc).isoformat()
                }
            }
        )
        if result.modified_count > 0:
            updated += result.modified_count
            return True
        return False
    
    print("=" * 60)
    print("ACTUALIZANDO PRECIOS MV - TARIFA 1")
    print("=" * 60)
    
    # 1. PUERTAS
    print("\n--- PUERTAS ---")
    for (code, height), price in PUERTAS_PRICES.items():
        if update_product(code, price, 'PUERTAS', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 2. VITRINA
    print("\n--- VITRINA ---")
    for (code, height), price in VITRINA_PRICES.items():
        if update_product(code, price, 'VITRINA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 3. REJILLA CONFESIONARIO
    print("\n--- REJILLA CONFESIONARIO ---")
    for (code, height), price in REJILLA_PRICES.items():
        if update_product(code, price, 'REJILLA CONFESIONARIO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 4. BAJOS
    print("\n--- BAJOS ---")
    for code, price in BAJO_PRICES.items():
        if update_product(code, price, 'BAJOS'):
            print(f"  {code}: {price} ✓")
    
    # 5. BAJO FREGADERO
    print("\n--- BAJO FREGADERO ---")
    for code, price in BAJO_FREGADERO_PRICES.items():
        if update_product(code, price, 'BAJO FREGADERO'):
            print(f"  {code}: {price} ✓")
    
    # 6. BAJO RINCON ESCUADRA
    print("\n--- BAJO RINCON ESCUADRA ---")
    for code, price in BAJO_RINCON_ESCUADRA_PRICES.items():
        if update_product(code, price, 'BAJO RINCON ESCUADRA'):
            print(f"  {code}: {price} ✓")
    
    # 7. BAJO RINCON CIEGO
    print("\n--- BAJO RINCON CIEGO ---")
    for code, price in BAJO_RINCON_CIEGO_PRICES.items():
        if update_product(code, price, 'BAJO RINCON CIEGO'):
            print(f"  {code}: {price} ✓")
    
    # 8. BAJO HORNO
    print("\n--- BAJO HORNO ---")
    for code, price in BAJO_HORNO_PRICES.items():
        if update_product(code, price, 'BAJO HORNO'):
            print(f"  {code}: {price} ✓")
    
    # 9. BAJO TERMINAL
    print("\n--- BAJO TERMINAL ---")
    for code, price in BAJO_TERMINAL_PRICES.items():
        if update_product(code, price, 'BAJO TERMINAL'):
            print(f"  {code}: {price} ✓")
    
    # 10. BAJO 2 GAVETAS+1FRENTE
    print("\n--- BAJO 2 GAVETAS+1 FRENTE ---")
    for code, price in BGF_PRICES.items():
        if update_product(code, price, 'BAJO 2 GAVETAS+1 FRENTE'):
            print(f"  {code}: {price} ✓")
    
    # 11. BAJO 2 CAJONES
    print("\n--- BAJO 2 CAJONES ---")
    for code, price in BCG_PRICES.items():
        if update_product(code, price, 'BAJO 2 CAJONES'):
            print(f"  {code}: {price} ✓")
    
    # 12. BAJO 3 CAJONES+1 GAVETA
    print("\n--- BAJO 3 CAJONES+1 GAVETA ---")
    for code, price in BCGC_PRICES.items():
        if update_product(code, price, 'BAJO 3 CAJONES+1 GAVETA'):
            print(f"  {code}: {price} ✓")
    
    # 13. BAJO PUERTA Y CAJON
    print("\n--- BAJO PUERTA Y CAJON ---")
    for code, price in BPC_PRICES.items():
        if update_product(code, price, 'BAJO PUERTA Y CAJON'):
            print(f"  {code}: {price} ✓")
    
    # 14. ALTOS (con altura)
    print("\n--- ALTOS ---")
    for (code, height), price in ALTO_PRICES.items():
        if update_product(code, price, 'ALTOS', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 15. ALTO CAMPANA
    print("\n--- ALTO CAMPANA ---")
    for (code, height), price in ALTO_CAMPANA_PRICES.items():
        if update_product(code, price, 'ALTO CAMPANA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 16. ALTO RINCON CIEGO
    print("\n--- ALTO RINCON CIEGO ---")
    for (code, height), price in ALTO_RINCON_CIEGO_PRICES.items():
        if update_product(code, price, 'ALTO RINCON CIEGO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 17. ALTO RINCON ESCUADRA
    print("\n--- ALTO RINCON ESCUADRA ---")
    for (code, height), price in ALTO_RINCON_ESCUADRA_PRICES.items():
        if update_product(code, price, 'ALTO RINCON ESCUADRA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 18. ALTO RINCON CHAFLAN
    print("\n--- ALTO RINCON CHAFLAN ---")
    for (code, height), price in ALTO_RINCON_CHAFLAN_PRICES.items():
        if update_product(code, price, 'ALTO RINCON CHAFLAN', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 19. ALTO DECORATIVO
    print("\n--- ALTO DECORATIVO ---")
    for (code, height), price in ALTO_DECORATIVO_PRICES.items():
        if update_product(code, price, 'ALTO DECORATIVO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 20. ALTO TERMINAL
    print("\n--- ALTO TERMINAL ---")
    for (code, height), price in ALTO_TERMINAL_PRICES.items():
        if update_product(code, price, 'ALTO TERMINAL', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 21. ALTO SOBREFRIGO
    print("\n--- ALTO SOBREFRIGO ---")
    for (code, height), price in ALTO_SOBREFRIGO_PRICES.items():
        if update_product(code, price, 'ALTO SOBREFRIGO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 22. ALTO CALDERA
    print("\n--- ALTO CALDERA ---")
    for (code, height), price in ALTO_CALDERA_PRICES.items():
        if update_product(code, price, 'ALTO CALDERA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 23. ALTO CALENTADOR
    print("\n--- ALTO CALENTADOR ---")
    for (code, height), price in ALTO_CALENTADOR_PRICES.items():
        if update_product(code, price, 'ALTO CALENTADOR', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 24. ALTO MICROONDAS
    print("\n--- ALTO MICROONDAS ---")
    for (code, height), price in ALTO_MICROONDAS_PRICES.items():
        if update_product(code, price, 'ALTO MICROONDAS', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 25. ALTO ESCURREPLATOS
    print("\n--- ALTO ESCURREPLATOS ---")
    for (code, height), price in ALTO_ESCURREPLATOS_PRICES.items():
        if update_product(code, price, 'ALTO ESCURREPLATOS', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 26. ALTO VITRINA
    print("\n--- ALTO VITRINA ---")
    for (code, height), price in ALTO_VITRINA_PRICES.items():
        if update_product(code, price, 'ALTO VITRINA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 27. ALTO ABATIBLE
    print("\n--- ALTO ABATIBLE ---")
    for (code, height), price in ALTO_ABATIBLE_PRICES.items():
        if update_product(code, price, 'ALTO ABATIBLE', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 28. ALTO COMBINADO PLUS
    print("\n--- ALTO COMBINADO PLUS ---")
    for (code, height), price in ALTO_COMBINADO_PLUS_PRICES.items():
        if update_product(code, price, 'ALTO COMBINADO PLUS', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 29. ALTILLO
    print("\n--- ALTILLO ---")
    for (code, height), price in ALTILLO_PRICES.items():
        if update_product(code, price, 'ALTILLO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 30. ALTILLO VITRINA
    print("\n--- ALTILLO VITRINA ---")
    for (code, height), price in ALTILLO_VITRINA_PRICES.items():
        if update_product(code, price, 'ALTILLO VITRINA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 31. SOBREENCIMERA
    print("\n--- SOBREENCIMERA ---")
    for (code, height), price in SOBREENCIMERA_PRICES.items():
        if update_product(code, price, 'SOBREENCIMERA', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 32. SOBREENCIMERA CAJON
    print("\n--- SOBREENCIMERA CAJON ---")
    for (code, height), price in SOBREENCIMERA_CAJON_PRICES.items():
        if update_product(code, price, 'SOBREENCIMERA CAJON', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 33. COLUMNA DESPENSERO
    print("\n--- COLUMNA DESPENSERO ---")
    for (code, height), price in COLUMNA_DESPENSERO_PRICES.items():
        if update_product(code, price, 'COLUMNA DESPENSERO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 34. COLUMNA FRIGO
    print("\n--- COLUMNA FRIGO ---")
    for (code, height), price in COLUMNA_FRIGO_PRICES.items():
        if update_product(code, price, 'COLUMNA FRIGO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 35. COLUMNA HORNO
    print("\n--- COLUMNA HORNO ---")
    for (code, height), price in COLUMNA_HORNO_PRICES.items():
        if update_product(code, price, 'COLUMNA HORNO', height):
            print(f"  {code} H{height}: {price} ✓")
    
    # 36. BOTELLEROS
    print("\n--- BOTELLEROS ---")
    for code, price in BOTELLERO_PRICES.items():
        if update_product(code, price, 'BOTELLEROS'):
            print(f"  {code}: {price} ✓")
    
    # 37. ALTILLOS DECORATIVOS
    print("\n--- ALTILLOS DECORATIVOS ---")
    for code, price in ALTILLOS_DECORATIVOS_PRICES.items():
        if update_product(code, price, 'ALTILLOS DECORATIVOS'):
            print(f"  {code}: {price} ✓")
    
    print("\n" + "=" * 60)
    print(f"TOTAL PRODUCTOS ACTUALIZADOS: {updated}")
    print("=" * 60)
    
    return updated


if __name__ == '__main__':
    update_prices()
