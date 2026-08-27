#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
AUDITORÍA Y CORRECCIÓN COMPLETA DE PRECIOS MV - TARIFA 1
Basado en PDFs escaneados de alta calidad proporcionados por el usuario
"""
import os
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# ============================================================================
# PÁGINA 1: PUERTAS, VITRINA, REJILLA CONFESIONARIO
# ============================================================================

PUERTAS = {
    ('P25', 14): 4, ('P25', 28): 5, ('P25', 40): 9, ('P25', 56): 10, ('P25', 70): 10, ('P25', 90): 13, ('P25', 127): 16, ('P25', 147): 19,
    ('P30', 14): 4, ('P30', 28): 6, ('P30', 40): 10, ('P30', 56): 11, ('P30', 70): 11, ('P30', 90): 14, ('P30', 127): 17, ('P30', 147): 20,
    ('P35', 14): 4, ('P35', 28): 6, ('P35', 40): 10, ('P35', 56): 11, ('P35', 70): 12, ('P35', 90): 15, ('P35', 127): 17, ('P35', 147): 21,
    ('P40', 14): 4, ('P40', 28): 7, ('P40', 40): 10, ('P40', 56): 11, ('P40', 70): 13, ('P40', 90): 15, ('P40', 127): 19, ('P40', 147): 22,
    ('P45', 14): 4, ('P45', 28): 7, ('P45', 40): 10, ('P45', 56): 11, ('P45', 70): 13, ('P45', 90): 16, ('P45', 127): 19, ('P45', 147): 22,
    ('P50', 14): 4, ('P50', 28): 7, ('P50', 40): 11, ('P50', 56): 13, ('P50', 70): 14, ('P50', 90): 17, ('P50', 127): 20, ('P50', 147): 23,
    ('P60', 14): 4, ('P60', 28): 8, ('P60', 40): 11, ('P60', 56): 13, ('P60', 70): 16, ('P60', 90): 19, ('P60', 127): 22, ('P60', 147): 26,
}

VITRINA = {
    ('PV30', 28): 20, ('PV30', 40): 34, ('PV30', 70): 40, ('PV30', 90): 49, ('PV30', 127): 68, ('PV30', 147): 77,
    ('PV35', 28): 22, ('PV35', 40): 36, ('PV35', 70): 43, ('PV35', 90): 52, ('PV35', 127): 72, ('PV35', 147): 82,
    ('PV40', 28): 23, ('PV40', 40): 37, ('PV40', 70): 45, ('PV40', 90): 54, ('PV40', 127): 76, ('PV40', 147): 87,
    ('PV45', 28): 24, ('PV45', 40): 38, ('PV45', 70): 47, ('PV45', 90): 57, ('PV45', 127): 81, ('PV45', 147): 92,
    ('PV50', 28): 25, ('PV50', 40): 40, ('PV50', 70): 49, ('PV50', 90): 59, ('PV50', 127): 85, ('PV50', 147): 97,
    ('PV60', 28): 28, ('PV60', 40): 42, ('PV60', 70): 54, ('PV60', 90): 65, ('PV60', 127): 89, ('PV60', 147): 118,
}

REJILLA_CONFESIONARIO = {
    ('PR30', 70): 41, ('PR30', 90): 51, ('PR30', 127): 55, ('PR30', 147): 63,
    ('PR35', 70): 45, ('PR35', 90): 55, ('PR35', 127): 60, ('PR35', 147): 69,
    ('PR40', 70): 48, ('PR40', 90): 60, ('PR40', 127): 67, ('PR40', 147): 76,
    ('PR45', 70): 51, ('PR45', 90): 65, ('PR45', 127): 71, ('PR45', 147): 82,
    ('PR50', 70): 56, ('PR50', 90): 68, ('PR50', 127): 78, ('PR50', 147): 88,
    ('PR60', 70): 63, ('PR60', 90): 78, ('PR60', 127): 89, ('PR60', 147): 109,
}

# ============================================================================
# PÁGINA 2: BAJOS (ya corregidos manualmente, solo verificación)
# ============================================================================

BAJOS = {
    'B25': 40, 'B30': 41, 'B35': 42, 'B40': 43, 'B45': 44, 'B50': 45,
    'B60': 49, 'B60 2P': 56, 'B70': 58, 'B80': 60, 'B90': 62, 'B100': 64,
}

BAJO_FREGADERO = {
    ('BF45', False): 41, ('BF50', False): 42, ('BF60', False): 46,
    ('BF60 2P', False): 52, ('BF70', False): 54, ('BF80', False): 56,
    ('BF90', False): 57, ('BF100', False): 59, ('BF120', False): 68,
    # Con chapa
    ('BF45', True): 47, ('BF50', True): 48, ('BF60', True): 52,
    ('BF60 2P', True): 59, ('BF70', True): 60, ('BF80', True): 63,
    ('BF90', True): 64, ('BF100', True): 67, ('BF120', True): 81,
}

BAJO_RINCON_ESCUADRA = {
    'BRI95': 88, 'BRU95': 87,
}

BAJO_RINCON_CIEGO = {
    'BR90': 62, 'BR95': 63, 'BR100': 64, 'BR105': 67, 'BR110': 68,
}

BAJO_HORNO = {
    'BH60': 37, 'BHC60': 45, 'BHZ60': 77, 'BHG60': 80,
}

BAJO_TERMINAL = {
    'BT30': 58, 'BTS30': 63, 'BTZ30': 72, 'BTP33': 65,
}

BAJO_PUERTA_CAJON = {
    'BPC30': 72, 'BPC35': 74, 'BPC40': 75, 'BPC45': 78, 'BPC50': 79, 'BPC60': 82,
    'BPC60 2P': 120, 'BPC70': 123, 'BPC80': 126, 'BPC90': 130, 'BPC100': 134,
}

BAJO_5_CAJONES = {
    'BC30': 168, 'BC35': 171, 'BC40': 173, 'BC45': 176, 'BC50': 179,
    'BC60': 184, 'BC70': 242, 'BC80': 246, 'BC90': 251,
}

BAJO_3_CAJONES_1_GAVETA = {
    'BCG30': 140, 'BCG35': 142, 'BCG40': 144, 'BCG45': 147, 'BCG50': 150,
    'BCG60': 154, 'BCG70': 199, 'BCG80': 203, 'BCG90': 208,
}

BAJO_2_CAJONES_1_GB = {
    'BGC30': 112, 'BGC35': 114, 'BGC40': 116, 'BGC45': 118, 'BGC50': 120,
    'BGC60': 124, 'BGC70': 146, 'BGC80': 150, 'BGC90': 155,
}

BAJO_2_GAVETAS_CAJON_FRENTE = {
    'BCGF60': 129, 'BCGF70': 153, 'BCGF80': 156, 'BCGF90': 159,
}

BAJO_2_GAVETAS_1_FRENTE = {
    'BGF60': 97, 'BGF70': 120, 'BGF80': 123, 'BGF90': 125, 'BGF120': 152,
}

# ============================================================================
# PÁGINA 3: ALTOS
# ============================================================================

ALTOS = {
    ('A25', 70): 38, ('A25', 90): 42,
    ('A30', 70): 39, ('A30', 90): 43,
    ('A35', 70): 40, ('A35', 90): 44,
    ('A40', 70): 41, ('A40', 90): 45,
    ('A45', 70): 42, ('A45', 90): 46,
    ('A50', 70): 44, ('A50', 90): 48,
    ('A60', 70): 47, ('A60', 90): 51,
    ('A60 2P', 70): 53, ('A60 2P', 90): 60,
    ('A70', 70): 56, ('A70', 90): 63,
    ('A80', 70): 58, ('A80', 90): 65,
    ('A90', 70): 59, ('A90', 90): 68,
    ('A100', 70): 62, ('A100', 90): 70,
}

ALTO_CAMPANA = {
    ('ASCE60', 70): 40, ('ASCE60', 90): 46,  # D/I extraplana
    ('ASCE60 2P', 70): 48, ('ASCE60 2P', 90): 52,  # extraplana
    ('ASCE90', 70): 53, ('ASCE90', 90): 58,  # extraplana
    ('ASC60', 70): 36, ('ASC60', 90): 42,  # D/I clásica
    ('ASC60 2P', 70): 43, ('ASC60 2P', 90): 48,  # clásica
}

ALTO_RINCON_CIEGO = {
    ('AR60', 70): 54, ('AR60', 90): 60,
    ('AR65', 70): 60, ('AR65', 90): 67,
}

ALTO_RINCON_ESCUADRA = {
    ('ARI65', 70): 84, ('ARI65', 90): 90,
    ('ARU65', 70): 82, ('ARU65', 90): 89,
}

ALTO_RINCON_CHAFLAN = {
    ('ARC63', 70): 54, ('ARC63', 90): 58,
    ('ARCV63', 70): 84, ('ARCV63', 90): 95,
}

ALTO_DECORATIVO = {
    ('AD40', 70): 36, ('AD40', 90): 43,
    ('AD45', 70): 37, ('AD45', 90): 44,
    ('AD50', 70): 39, ('AD50', 90): 47,
    ('AD60', 70): 42, ('AD60', 90): 51,
    ('AD70', 70): 46, ('AD70', 90): 55,
    ('AD80', 70): 48, ('AD80', 90): 59,
    ('AD90', 70): 52, ('AD90', 90): 64,
    ('AD100', 70): 55, ('AD100', 90): 68,
}

ALTO_VITRINA = {
    ('AV30', 70): 68, ('AV30', 90): 77,
    ('AV35', 70): 70, ('AV35', 90): 80,
    ('AV40', 70): 72, ('AV40', 90): 83,
    ('AV45', 70): 75, ('AV45', 90): 86,
    ('AV50', 70): 78, ('AV50', 90): 89,
    ('AV60', 70): 84, ('AV60', 90): 96,
    ('AV60 2P', 70): 110, ('AV60 2P', 90): 128,
    ('AV70', 70): 116, ('AV70', 90): 135,
    ('AV80', 70): 120, ('AV80', 90): 140,
    ('AV90', 70): 125, ('AV90', 90): 146,
    ('AV100', 70): 131, ('AV100', 90): 152,
}

ALTO_ESCURREPLATOS = {
    ('AE45', 70): 50, ('AE45', 90): 57,
    ('AE50', 70): 53, ('AE50', 90): 60,
    ('AE60', 70): 57, ('AE60', 90): 63,
    ('AE60 2P', 70): 64, ('AE60 2P', 90): 74,
    ('AE70', 70): 67, ('AE70', 90): 77,
    ('AE80', 70): 70, ('AE80', 90): 80,
    ('AE90', 70): 73, ('AE90', 90): 84,
    ('AE100', 70): 76, ('AE100', 90): 88,
}

ALTO_MICROONDAS = {
    ('AM60', 70): 40, ('AM60', 90): 45,
    ('AM60 2P', 70): 47, ('AM60 2P', 90): 52,
    ('AMF60', 70): 47, ('AMF60', 90): 52,
    ('AMF60 2P', 70): 54, ('AMF60 2P', 90): 59,
}

ALTO_CALENTADOR = {
    ('ACA45', 70): 36, ('ACA45', 90): 40,
    ('ACA50', 70): 37, ('ACA50', 90): 41,
    ('ACA60', 70): 40, ('ACA60', 90): 42,
    ('ACA60 2P', 70): 46, ('ACA60 2P', 90): 52,
}

ALTO_CALDERA = {
    ('ACC60', 70): 49, ('ACC60', 90): 51,
    ('ACC60 2P', 70): 58, ('ACC60 2P', 90): 60,
}

ALTO_SOBREFRIGO = {
    ('ASF60', 70): 39, ('ASF60', 90): 45,
    ('ASF60 2P', 70): 46, ('ASF60 2P', 90): 51,
    ('ASF60A', 70): 49, ('ASF60A', 90): 55,
    ('ASF60F', 70): 69, ('ASF60F', 90): 75,
}

ALTO_TERMINAL = {
    ('AT30', 70): 52, ('AT30', 90): 64,
    ('ATP33', 70): 63, ('ATP33', 90): 71,
}

# ============================================================================
# PÁGINA 4: MÁS ALTOS Y OTROS
# ============================================================================

ALTO_ABATIBLE = {
    ('AA45', 70): 95, ('AA45', 90): 99,
    ('AA50', 70): 97, ('AA50', 90): 101,
    ('AA60', 70): 106, ('AA60', 90): 113,
    ('AA70', 70): 109, ('AA70', 90): 116,
    ('AA80', 70): 110, ('AA80', 90): 118,
    ('AA90', 70): 111, ('AA90', 90): 121,
    ('AA100', 70): 115, ('AA100', 90): 123,
}

ALTO_COMBINADO_PLUS = {
    ('ACP45', 70): 127, ('ACP45', 90): 139,
    ('ACP50', 70): 129, ('ACP50', 90): 142,
    ('ACP60', 70): 138, ('ACP60', 90): 154,
    ('ACP70', 70): 141, ('ACP70', 90): 156,
    ('ACP80', 70): 149, ('ACP80', 90): 158,
    ('ACP90', 70): 150, ('ACP90', 90): 165,
    ('ACP100', 70): 152, ('ACP100', 90): 169,
}

ALTILLO = {
    ('L30', 70): 65, ('L30', 90): 69,
    ('L35', 70): 66, ('L35', 90): 70,
    ('L40', 70): 66, ('L40', 90): 71,
    ('L45', 70): 67, ('L45', 90): 72,
    ('L50', 70): 68, ('L50', 90): 73,
    ('L60', 70): 69, ('L60', 90): 78,
    ('L70', 70): 71, ('L70', 90): 80,
    ('L80', 70): 73, ('L80', 90): 82,
    ('L90', 70): 75, ('L90', 90): 84,
    ('L100', 70): 77, ('L100', 90): 86,
}

SOBREENCIMERA = {
    ('S30', 127): 51, ('S30', 147): 54,
    ('S35', 127): 52, ('S35', 147): 56,
    ('S40', 127): 54, ('S40', 147): 58,
    ('S45', 127): 56, ('S45', 147): 59,
    ('S50', 127): 57, ('S50', 147): 62,
    ('S60', 127): 60, ('S60', 147): 65,
    ('S60 2P', 127): 71, ('S60 2P', 147): 77,
}

SOBREENC_CAJON = {
    ('SC30', 127): 72, ('SC30', 147): 76,
    ('SC35', 127): 74, ('SC35', 147): 78,
    ('SC40', 127): 76, ('SC40', 147): 80,
    ('SC45', 127): 78, ('SC45', 147): 82,
    ('SC50', 127): 80, ('SC50', 147): 84,
    ('SC60', 127): 83, ('SC60', 147): 88,
    ('SC60 2P', 127): 94, ('SC60 2P', 147): 100,
}

ALTILLO_VITRINA = {
    ('LV30', 70): 88, ('LV30', 90): 98,
    ('LV35', 70): 92, ('LV35', 90): 101,
    ('LV40', 70): 93, ('LV40', 90): 103,
    ('LV45', 70): 95, ('LV45', 90): 106,
    ('LV50', 70): 97, ('LV50', 90): 108,
    ('LV60', 70): 100, ('LV60', 90): 116,
    ('LV70', 70): 103, ('LV70', 90): 118,
    ('LV80', 70): 105, ('LV80', 90): 120,
    ('LV90', 70): 107, ('LV90', 90): 123,
    ('LV100', 70): 109, ('LV100', 90): 126,
}

SOBREENC_VITRINA = {
    ('SV30', 127): 101, ('SV30', 147): 111,
    ('SV35', 127): 106, ('SV35', 147): 117,
    ('SV40', 127): 111, ('SV40', 147): 121,
    ('SV45', 127): 115, ('SV45', 147): 127,
    ('SV50', 127): 120, ('SV50', 147): 132,
    ('SV60', 127): 125, ('SV60', 147): 155,
    ('SV60 2P', 127): 170, ('SV60 2P', 147): 189,
}

SOBREENC_VIT_CAJON = {
    ('SVC30', 127): 122, ('SVC30', 147): 132,
    ('SVC35', 127): 128, ('SVC35', 147): 138,
    ('SVC40', 127): 132, ('SVC40', 147): 143,
    ('SVC45', 127): 137, ('SVC45', 147): 149,
    ('SVC50', 127): 143, ('SVC50', 147): 155,
    ('SVC60', 127): 149, ('SVC60', 147): 178,
    ('SVC60 2P', 127): 203, ('SVC60 2P', 147): 223,
}

ALTO_COMBINADO = {
    ('AC45', 70): 127, ('AC45', 90): 137,
    ('AC50', 70): 127, ('AC50', 90): 137,
    ('AC60', 70): 136, ('AC60', 90): 149,
    ('AC70', 70): 139, ('AC70', 90): 150,
    ('AC80', 70): 147, ('AC80', 90): 159,
    ('AC90', 70): 148, ('AC90', 90): 162,
    ('AC100', 70): 168, ('AC100', 90): 185,
}

ALTO_COMBINADO_PLUS_J = {
    ('ACPJ45', 70): 134, ('ACPJ45', 90): 146,
    ('ACPJ50', 70): 134, ('ACPJ50', 90): 149,
    ('ACPJ60', 70): 143, ('ACPJ60', 90): 158,
    ('ACPJ70', 70): 146, ('ACPJ70', 90): 160,
    ('ACPJ80', 70): 158, ('ACPJ80', 90): 165,
    ('ACPJ90', 70): 159, ('ACPJ90', 90): 172,
    ('ACPJ100', 70): 161, ('ACPJ100', 90): 176,
}

# ============================================================================
# PÁGINA 5: COLUMNAS
# ============================================================================

COLUMNA_DESPENSERO = {
    ('CD30', 200): 90, ('CD30', 220): 94,
    ('CD35', 200): 94, ('CD35', 220): 97,
    ('CD40', 200): 96, ('CD40', 220): 101,
    ('CD45', 200): 99, ('CD45', 220): 103,
    ('CD50', 200): 102, ('CD50', 220): 107,
    ('CD60', 200): 109, ('CD60', 220): 112,
    ('CD60 2P', 200): 125, ('CD60 2P', 220): 132,
    ('CD70', 200): 145, ('CD70', 220): 152,
    ('CD80', 200): 163, ('CD80', 220): 170,
    ('CD90', 200): 184, ('CD90', 220): 191,
}

COLUMNA_FRIGO = {
    ('CF60', 200): 63, ('CF60', 220): 69,
    ('CF60 2P', 200): 72, ('CF60 2P', 220): 75,
    ('CF60A', 200): 73, ('CF60A', 220): 79,
    ('CF60F', 200): 93, ('CF60F', 220): 99,
}

COLUMNA_HORNO = {
    ('CH60', 200): 97, ('CH60', 220): 101,
    ('CH60 2P', 200): 110, ('CH60 2P', 220): 117,
    ('CHPC60', 200): 129, ('CHPC60', 220): 134,
    ('CHPC60 2P', 200): 143, ('CHPC60 2P', 220): 151,
    ('CHGC60', 200): 167, ('CHGC60', 220): 172,
    ('CHGC60 2P', 200): 173, ('CHGC60 2P', 220): 181,
    ('CHC60', 200): 234, ('CHC60', 220): 237,
    ('CHC60 2P', 200): 240, ('CHC60 2P', 220): 246,
}

COLUMNA_HORNO_MICRO = {
    ('CHM60', 200): 92, ('CHM60', 220): 97,
    ('CHM60 2P', 200): 106, ('CHM60 2P', 220): 112,
    ('CHMG60', 200): 132, ('CHMG60', 220): 137,
    ('CHMG60 2P', 200): 140, ('CHMG60 2P', 220): 144,
    ('CHMC60', 200): 197, ('CHMC60', 220): 202,
    ('CHMC60 2P', 200): 205, ('CHMC60 2P', 220): 210,
    ('CHMCG60', 200): 162, ('CHMCG60', 220): 167,
    ('CHMCG60 2P', 200): 170, ('CHMCG60 2P', 220): 174,
}

MEDIACOLUMNA = {
    'M30': 58, 'M35': 59, 'M40': 62, 'M45': 63, 'M50': 65, 'M60': 69, 'M60 2P': 79,
}

MEDIA_PUERTA_GAVETA = {
    'MPG30': 83, 'MPG35': 85, 'MPG40': 87, 'MPG45': 89, 'MPG50': 92, 'MPG60': 95, 'MPG60 2P': 105,
}

MEDIACOLUMNA_HORNO = {
    'MPH60': 61, 'MPH60 2P': 68, 'MPM60': 64, 'MPM60 2P': 73, 'MGHM60': 86, 'MCHM60': 117,
}

BOTELLEROS = {
    ('BOA', 70): 41, ('BOA', 90): 47,
    ('BOS', 127): 60, ('BOS', 147): 66,
    ('BOC', 200): 83, ('BOC', 220): 88,
}

MEDIACOLUMNA_VITRINA = {
    'MV30': 107, 'MV35': 113, 'MV40': 118, 'MV45': 123, 'MV50': 128, 'MV60': 134, 'MV60 2P': 179,
}

MEDIACOL_VITRINA_GAVETA = {
    'MVG30': 125, 'MVG35': 131, 'MVG40': 136, 'MVG45': 141, 'MVG50': 146, 'MVG60': 159, 'MVG60 2P': 190,
}

ALTILLOS_DECORATIVOS = {
    'LD30': 23, 'LD35': 24, 'LD40': 25, 'LD45': 26, 'LD50': 27,
    'LD60': 29, 'LD70': 30, 'LD80': 33, 'LD90': 34, 'LD100': 36,
}


def audit_and_correct():
    """Auditar y corregir todos los precios MV"""
    
    total_checked = 0
    total_errors = 0
    total_corrected = 0
    
    def check_and_update(code, correct_price, series, height=None, width=None):
        nonlocal total_checked, total_errors, total_corrected
        
        query = {'library': 'MV', 'code': code, 'series': series}
        if height:
            query['height'] = height
            
        products = list(db.products.find(query))
        total_checked += 1
        
        if not products:
            return None, 'NOT_FOUND'
            
        current_price = products[0].get('points', 0)
        if current_price != correct_price:
            total_errors += 1
            # Corregir
            result = db.products.update_many(
                query,
                {'$set': {
                    'points': float(correct_price),
                    'zonePoints.T1': float(correct_price),
                    'updatedAt': datetime.now(timezone.utc).isoformat()
                }}
            )
            total_corrected += result.modified_count
            return current_price, 'CORRECTED'
        return current_price, 'OK'
    
    print("=" * 80)
    print("AUDITORÍA COMPLETA DE PRECIOS MV - TARIFA 1")
    print("=" * 80)
    
    # Auditar ALTOS
    print("\n### ALTOS ###")
    for (code, height), correct_price in ALTOS.items():
        current, status = check_and_update(code, correct_price, 'ALTOS', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
        elif status == 'NOT_FOUND':
            print(f"  ⚠️  {code} H{height}: NO ENCONTRADO")
    
    # Auditar ALTO DECORATIVO
    print("\n### ALTO DECORATIVO ###")
    for (code, height), correct_price in ALTO_DECORATIVO.items():
        current, status = check_and_update(code, correct_price, 'ALTO DECORATIVO', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTO VITRINA
    print("\n### ALTO VITRINA ###")
    for (code, height), correct_price in ALTO_VITRINA.items():
        current, status = check_and_update(code, correct_price, 'ALTO VITRINA', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTO ESCURREPLATOS
    print("\n### ALTO ESCURREPLATOS ###")
    for (code, height), correct_price in ALTO_ESCURREPLATOS.items():
        current, status = check_and_update(code, correct_price, 'ALTO ESCURREPLATOS', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTO ABATIBLE
    print("\n### ALTO ABATIBLE ###")
    for (code, height), correct_price in ALTO_ABATIBLE.items():
        current, status = check_and_update(code, correct_price, 'ALTO ABATIBLE', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTO COMBINADO PLUS
    print("\n### ALTO COMBINADO PLUS ###")
    for (code, height), correct_price in ALTO_COMBINADO_PLUS.items():
        current, status = check_and_update(code, correct_price, 'ALTO COMBINADO PLUS', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTILLO
    print("\n### ALTILLO ###")
    for (code, height), correct_price in ALTILLO.items():
        current, status = check_and_update(code, correct_price, 'ALTILLO', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar ALTILLO VITRINA
    print("\n### ALTILLO VITRINA ###")
    for (code, height), correct_price in ALTILLO_VITRINA.items():
        current, status = check_and_update(code, correct_price, 'ALTILLO VITRINA', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar COLUMNA DESPENSERO
    print("\n### COLUMNA DESPENSERO ###")
    for (code, height), correct_price in COLUMNA_DESPENSERO.items():
        current, status = check_and_update(code, correct_price, 'COLUMNA DESPENSERO', height)
        if status == 'CORRECTED':
            print(f"  ❌ {code} H{height}: {current} → {correct_price} (CORREGIDO)")
    
    # Auditar BAJO RINCON CIEGO
    print("\n### BAJO RINCON CIEGO ###")
    for code, correct_price in BAJO_RINCON_CIEGO.items():
        for h in [70, 80]:
            current, status = check_and_update(code, correct_price, 'BAJO RINCON CIEGO', h)
            if status == 'CORRECTED':
                print(f"  ❌ {code} H{h}: {current} → {correct_price} (CORREGIDO)")
    
    print("\n" + "=" * 80)
    print(f"RESUMEN:")
    print(f"  Productos verificados: {total_checked}")
    print(f"  Errores encontrados: {total_errors}")
    print(f"  Documentos corregidos: {total_corrected}")
    print("=" * 80)
    
    return total_errors, total_corrected


if __name__ == '__main__':
    errors, corrected = audit_and_correct()
    print(f"\nAuditoría completada. {errors} errores encontrados, {corrected} documentos corregidos.")
