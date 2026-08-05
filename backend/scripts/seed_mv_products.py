#!/usr/bin/env python3
# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Script to seed MV library products from TARIFA 1
Run this script to populate the MongoDB database with MV products
"""
import os
import sys
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

def main():
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("ERROR: MONGO_URL not set")
        sys.exit(1)
        
    client = MongoClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'luiggi_home')]

    now = datetime.now(timezone.utc)
    products_to_insert = []

    def create_product(code, name, category, t1_price, height=None, width=None, depth=0, series=None):
        """Helper to create a product document"""
        return {
            "id": f"prod-mv-{uuid.uuid4().hex[:8]}",
            "code": code,
            "name": name,
            "category": category,
            "type": category,
            "series": series or f"{category} MV",
            "visualType": "standard",
            "width": float(width) if width else 0,
            "height": float(height) if height else 0,
            "depth": float(depth) if depth else 0,
            "manufacturer": "Mueble Montada",
            "module": "montada",
            "library": "MV",
            "points": float(t1_price),
            "zonePoints": {"T1": float(t1_price)},
            "catalogId": "cat-m-base",
            "sourceFile": "TARIFA_1_MV",
            "createdAt": now,
            "updatedAt": now
        }

    # ==================== PÁGINA 1 ====================
    # PUERTAS (P25-P60)
    puertas_data = {
        25: {70: 10, 90: 13},
        30: {14: 4, 28: 5, 40: 9, 56: 10, 70: 11, 90: 14, 127: 16, 147: 19},
        35: {14: 4, 28: 6, 40: 10, 56: 11, 70: 12, 90: 15, 127: 17, 147: 20},
        40: {14: 4, 28: 6, 40: 10, 56: 11, 70: 13, 90: 15, 127: 19, 147: 21},
        45: {14: 4, 28: 7, 40: 10, 56: 11, 70: 13, 90: 16, 127: 19, 147: 22},
        50: {14: 4, 28: 7, 40: 11, 56: 13, 70: 14, 90: 17, 127: 20, 147: 23},
        60: {14: 4, 28: 8, 40: 11, 56: 13, 70: 16, 90: 19, 127: 22, 147: 26},
    }
    for width, heights in puertas_data.items():
        for height, t1 in heights.items():
            products_to_insert.append(create_product(f"P{width}", f"PUERTA {width} CM x H{height}", "PUERTAS", t1, height, width))

    # VITRINA (PV30-PV60)
    vitrina_data = {
        30: {28: 20, 40: 34, 70: 40, 90: 49, 127: 68, 147: 77},
        35: {28: 22, 40: 36, 70: 43, 90: 52, 127: 72, 147: 82},
        40: {28: 23, 40: 37, 70: 45, 90: 54, 127: 76, 147: 87},
        45: {28: 24, 40: 38, 70: 47, 90: 57, 127: 81, 147: 92},
        50: {28: 25, 40: 40, 70: 49, 90: 59, 127: 85, 147: 97},
        60: {28: 28, 40: 42, 70: 54, 90: 65, 127: 89, 147: 118},
    }
    for width, heights in vitrina_data.items():
        for height, t1 in heights.items():
            products_to_insert.append(create_product(f"PV{width}", f"VITRINA {width} CM x H{height}", "VITRINA", t1, height, width))

    # REJILLA CONFESIONARIO (PR30-PR60)
    rejilla_data = {
        30: {70: 41, 90: 51, 127: 55, 147: 63},
        35: {70: 45, 90: 55, 127: 60, 147: 69},
        40: {70: 48, 90: 60, 127: 67, 147: 76},
        45: {70: 51, 90: 65, 127: 71, 147: 82},
        50: {70: 56, 90: 68, 127: 78, 147: 88},
        60: {70: 63, 90: 78, 127: 89, 147: 109},
    }
    for width, heights in rejilla_data.items():
        for height, t1 in heights.items():
            products_to_insert.append(create_product(f"PR{width}", f"REJILLA CONFESIONARIO {width} CM x H{height}", "REJILLA CONFESIONARIO", t1, height, width))

    # ==================== PÁGINA 2 - BAJOS ====================
    # BAJO básico
    bajo_basic = [
        ("B25D/I", "BAJO 25 D/I", 30), ("B30D/I", "BAJO 30 D/I", 35), 
        ("B35D/I", "BAJO 35 D/I", 40), ("B40D/I", "BAJO 40 D/I", 41),
        ("B45D/I", "BAJO 45 D/I", 42), ("B50D/I", "BAJO 50 D/I", 43),
        ("B60D/I", "BAJO 60 D/I", 44), ("B60", "BAJO 60", 45),
        ("B70", "BAJO 70", 49), ("B80", "BAJO 80", 56),
        ("B90", "BAJO 90", 58), ("B100", "BAJO 100", 60)
    ]
    for code, name, t1 in bajo_basic:
        products_to_insert.append(create_product(code, name, "BAJOS", t1))

    # BAJO FREGADERO  
    bajo_fregadero = [
        ("BF45D/I", "BAJO FREGADERO 45 D/I", 41),
        ("BF50D/I", "BAJO FREGADERO 50 D/I", 47),
        ("BF60D/I", "BAJO FREGADERO 60 D/I", 52),
        ("BF70", "BAJO FREGADERO 70", 54),
        ("BF80", "BAJO FREGADERO 80", 57),
        ("BF90", "BAJO FREGADERO 90", 59),
        ("BF100", "BAJO FREGADERO 100", 67),
        ("BF120", "BAJO FREGADERO 120", 68)
    ]
    for code, name, t1 in bajo_fregadero:
        products_to_insert.append(create_product(code, name, "BAJO FREGADERO", t1))

    # BAJO RINCON ESCUADRA 
    bajo_rincon_escuadra = [
        ("BR195D/I", "BAJO RINCON ESCUADRA 93x95", 87),
        ("BRU95D/I", "BAJO RINCON ESCUADRA 95x95 UNIDAS", 88),
    ]
    for code, name, t1 in bajo_rincon_escuadra:
        products_to_insert.append(create_product(code, name, "BAJO RINCON ESCUADRA", t1))

    # BAJO RINCON CIEGO
    bajo_rincon_ciego = [
        ("BR90D/I", "BAJO RINCON CIEGO 90 PTA 30", 81),
        ("BR95D/I", "BAJO RINCON CIEGO 95 PTA 30", 87),
        ("BR100D/I", "BAJO RINCON CIEGO 100 PTA 30", 88),
        ("BR105D/I", "BAJO RINCON CIEGO 105 PTA 30", 65),
        ("BR110D/I", "BAJO RINCON CIEGO 110 PTA 30", 72),
    ]
    for code, name, t1 in bajo_rincon_ciego:
        products_to_insert.append(create_product(code, name, "BAJO RINCON CIEGO", t1))

    # BAJO HORNO
    bajo_horno = [
        ("BH60", "BAJO HORNO 60", 37),
        ("BHC60", "BAJO HORNO 60 CON CAJON", 45),
        ("BHZ60", "BAJO HORNO 60 CON ZOCALO", 77),
        ("BHG60", "BAJO HORNO 60 CON GAVETA", 80),
    ]
    for code, name, t1 in bajo_horno:
        products_to_insert.append(create_product(code, name, "BAJO HORNO", t1))

    # BAJO TERMINAL
    bajo_terminal = [
        ("BT530D/I", "BAJO TERMINAL 30 D/I LATS SUP", 60),
        ("BTZ30D/I", "BAJO TERMINAL 30 D/I CON ZOCALO", 60),
        ("BTP33D/I", "BAJO TERMINAL 33 D/I", 63),
    ]
    for code, name, t1 in bajo_terminal:
        products_to_insert.append(create_product(code, name, "BAJO TERMINAL", t1))

    # BAJO PUERTA Y CAJON
    bajo_puerta_cajon = [
        ("BPC30D/I", "BAJO PUERTA Y CAJON 30 D/I", 74),
        ("BPC35D/I", "BAJO PUERTA Y CAJON 35 D/I", 75),
        ("BPC40D/I", "BAJO PUERTA Y CAJON 40 D/I", 78),
        ("BPC45D/I", "BAJO PUERTA Y CAJON 45 D/I", 79),
        ("BPC50D/I", "BAJO PUERTA Y CAJON 50 D/I", 82),
        ("BPC60D/I", "BAJO PUERTA Y CAJON 60 D/I", 120),
        ("BPC70", "BAJO PUERTA Y CAJON 70", 123),
        ("BPC80", "BAJO PUERTA Y CAJON 80", 126),
        ("BPC90", "BAJO PUERTA Y CAJON 90", 130),
        ("BPC100", "BAJO PUERTA Y CAJON 100", 134),
    ]
    for code, name, t1 in bajo_puerta_cajon:
        products_to_insert.append(create_product(code, name, "BAJO PUERTA Y CAJON", t1))

    # BAJO 2 GAVETAS+1 FRENTE
    bajo_2_gavetas_frente = [
        ("BGF70", "BAJO 2 GAVETAS+1 FRENTE 70", 156),
        ("BGF80", "BAJO 2 GAVETAS+1 FRENTE 80", 157),
        ("BGF90", "BAJO 2 GAVETAS+1 FRENTE 90", 159),
        ("BGF120", "BAJO 2 GAVETAS+1 FRENTE 120", 168),
    ]
    for code, name, t1 in bajo_2_gavetas_frente:
        products_to_insert.append(create_product(code, name, "BAJO 2 GAVETAS+1 FRENTE", t1))

    # BAJO 2 CAJONES
    bajo_2_cajones = [
        ("BC30", "BAJO 2 CAJONES 30", 112),
        ("BC35", "BAJO 2 CAJONES 35", 114),
        ("BC40", "BAJO 2 CAJONES 40", 116),
        ("BC45", "BAJO 2 CAJONES 45", 118),
        ("BC50", "BAJO 2 CAJONES 50", 120),
        ("BC60", "BAJO 2 CAJONES 60", 124),
        ("BC70", "BAJO 2 CAJONES 70", 126),
        ("BC80", "BAJO 2 CAJONES 80", 129),
        ("BC90", "BAJO 2 CAJONES 90", 130),
    ]
    for code, name, t1 in bajo_2_cajones:
        products_to_insert.append(create_product(code, name, "BAJO 2 CAJONES", t1))

    # BAJO 2 GAVETAS+1 CAJON
    bajo_2_gavetas_cajon = [
        ("BCG30", "BAJO 2 GAVETAS+1 CAJON 30", 140),
        ("BCG35", "BAJO 2 GAVETAS+1 CAJON 35", 142),
        ("BCG40", "BAJO 2 GAVETAS+1 CAJON 40", 144),
        ("BCG45", "BAJO 2 GAVETAS+1 CAJON 45", 146),
        ("BCG50", "BAJO 2 GAVETAS+1 CAJON 50", 150),
        ("BCG60", "BAJO 2 GAVETAS+1 CAJON 60", 155),
    ]
    for code, name, t1 in bajo_2_gavetas_cajon:
        products_to_insert.append(create_product(code, name, "BAJO 2 GAVETAS+1 CAJON", t1))

    # BAJO 3 CAJONES+1 GAVETA
    bajo_3_cajones_gaveta = [
        ("BCGF30", "BAJO 3 CAJONES+1 GAVETA 30", 140),
        ("BCGF35", "BAJO 3 CAJONES+1 GAVETA 35", 142),
        ("BCGF40", "BAJO 3 CAJONES+1 GAVETA 40", 144),
        ("BCGF45", "BAJO 3 CAJONES+1 GAVETA 45", 147),
        ("BCGF50", "BAJO 3 CAJONES+1 GAVETA 50", 150),
        ("BCGF60", "BAJO 3 CAJONES+1 GAVETA 60", 154),
        ("BCGF70", "BAJO 3 CAJONES+1 GAVETA 70", 199),
        ("BCGF80", "BAJO 3 CAJONES+1 GAVETA 80", 203),
        ("BCGF90", "BAJO 3 CAJONES+1 GAVETA 90", 208),
    ]
    for code, name, t1 in bajo_3_cajones_gaveta:
        products_to_insert.append(create_product(code, name, "BAJO 3 CAJONES+1 GAVETA", t1))

    # ==================== PÁGINA 3 - ALTOS ====================
    # ALTO básico - H70 y H90
    alto_basic_h70 = [
        ("A25D/I", "ALTO 25 D/I H70", 36), ("A30D/I", "ALTO 30 D/I H70", 36),
        ("A35D/I", "ALTO 35 D/I H70", 37), ("A40D/I", "ALTO 40 D/I H70", 39),
        ("A45D/I", "ALTO 45 D/I H70", 42), ("A50D/I", "ALTO 50 D/I H70", 47),
        ("A60D/I", "ALTO 60 D/I H70", 51), ("A70", "ALTO 70 H70", 55),
        ("A80", "ALTO 80 H70", 62), ("A90", "ALTO 90 H70", 68),
        ("A100", "ALTO 100 H70", 62),
    ]
    for code, name, t1 in alto_basic_h70:
        products_to_insert.append(create_product(code, name, "ALTOS", t1, height=70))
    
    alto_basic_h90 = [
        ("A25D/I", "ALTO 25 D/I H90", 38), ("A30D/I", "ALTO 30 D/I H90", 42),
        ("A35D/I", "ALTO 35 D/I H90", 43), ("A40D/I", "ALTO 40 D/I H90", 45),
        ("A45D/I", "ALTO 45 D/I H90", 46), ("A50D/I", "ALTO 50 D/I H90", 51),
        ("A60D/I", "ALTO 60 D/I H90", 58), ("A70", "ALTO 70 H90", 65),
        ("A80", "ALTO 80 H90", 66), ("A90", "ALTO 90 H90", 70),
        ("A100", "ALTO 100 H90", 70),
    ]
    for code, name, t1 in alto_basic_h90:
        products_to_insert.append(create_product(code, name, "ALTOS", t1, height=90))

    # ALTO CAMPANA
    alto_campana = [
        ("ASCE60D/I", "ALTO CAMPANA EXTRAPLANA 60 D/I", 70),
        ("ASCE60", "ALTO CAMPANA EXTRAPLANA 60", 40),
        ("ASCE90", "ALTO CAMPANA EXTRAPLANA 90", 46),
        ("ASC60D/I", "ALTO CAMPANA CLASICA 60 D/I", 53),
        ("ASC60", "ALTO CAMPANA CLASICA 60", 52),
    ]
    for code, name, t1 in alto_campana:
        products_to_insert.append(create_product(code, name, "ALTO CAMPANA", t1))

    # ALTO RINCON CIEGO
    alto_rincon_ciego = [
        ("AR60D/I", "ALTO RINCON CIEGO 60 D/I PTA 25 H70", 54, 70),
        ("AR65D/I", "ALTO RINCON CIEGO 65 D/I PTA 30 H70", 60, 70),
        ("AR60D/I", "ALTO RINCON CIEGO 60 D/I PTA 25 H90", 67, 90),
        ("AR65D/I", "ALTO RINCON CIEGO 65 D/I PTA 30 H90", 70, 90),
    ]
    for item in alto_rincon_ciego:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO RINCON CIEGO", t1, height=h))

    # ALTO RINCON ESCUADRA
    alto_rincon_escuadra = [
        ("ARU65D/I", "ALTO RINCON ESCUADRA 65 D/I PTAS UNIDAS H70", 82, 70),
        ("ARI65D/I", "ALTO RINCON ESCUADRA 65 D/I PTAS INDEP H70", 84, 70),
        ("ARU65D/I", "ALTO RINCON ESCUADRA 65 D/I PTAS UNIDAS H90", 89, 90),
        ("ARI65D/I", "ALTO RINCON ESCUADRA 65 D/I PTAS INDEP H90", 89, 90),
    ]
    for item in alto_rincon_escuadra:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO RINCON ESCUADRA", t1, height=h))

    # ALTO RINCON CHAFLAN
    alto_rincon_chaflan = [
        ("ARC63D/I", "ALTO RINCON CHAFLAN 63 D/I H70", 70, 70),
        ("ARCV63D/I", "ALTO RINCON CHAFLAN VITRINA 63 D/I H70", 84, 70),
        ("ARC63D/I", "ALTO RINCON CHAFLAN 63 D/I H90", 55, 90),
        ("ARCV63D/I", "ALTO RINCON CHAFLAN VITRINA 63 D/I H90", 95, 90),
    ]
    for item in alto_rincon_chaflan:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO RINCON CHAFLAN", t1, height=h))

    # ALTO DECORATIVO
    alto_decorativo = [
        ("AD40", "ALTO DECORATIVO 40", 36), ("AD45", "ALTO DECORATIVO 45", 37),
        ("AD50", "ALTO DECORATIVO 50", 39), ("AD60", "ALTO DECORATIVO 60", 42),
        ("AD70", "ALTO DECORATIVO 70", 46), ("AD80", "ALTO DECORATIVO 80", 48),
        ("AD90", "ALTO DECORATIVO 90", 52), ("AD100", "ALTO DECORATIVO 100", 55),
    ]
    for code, name, t1 in alto_decorativo:
        products_to_insert.append(create_product(code, name, "ALTO DECORATIVO", t1))

    # ALTO TERMINAL - H70 y H90
    alto_terminal = [
        ("ATP30D/I", "ALTO TERMINAL 30 D/I H70", 52, 70),
        ("ATP33D/I", "ALTO TERMINAL 33 D/I H70", 63, 70),
        ("ATP30D/I", "ALTO TERMINAL 30 D/I H90", 64, 90),
        ("ATP33D/I", "ALTO TERMINAL 33 D/I H90", 71, 90),
    ]
    for item in alto_terminal:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO TERMINAL", t1, height=h))

    # ALTO SOBREFRIGO
    alto_sobrefrigo = [
        ("ASF60D/I", "ALTO SOBREFRIGO 60 D/I ABAT SALVACEJAS H70", 39, 70),
        ("ASF60", "ALTO SOBREFRIGO 60 H70", 46, 70),
        ("ASF60A", "ALTO SOBREFRIGO 60 ABAT H70", 49, 70),
        ("ASF60F", "ALTO SOBREFRIGO 60 ABAT FREEZER", 69),
    ]
    for item in alto_sobrefrigo:
        if len(item) == 4:
            code, name, t1, h = item
            products_to_insert.append(create_product(code, name, "ALTO SOBREFRIGO", t1, height=h))
        else:
            code, name, t1 = item
            products_to_insert.append(create_product(code, name, "ALTO SOBREFRIGO", t1))

    # ALTO CALDERA
    alto_caldera = [
        ("ACC60D/I", "ALTO CALDERA 60 D/I H70", 49, 70),
        ("ACC60", "ALTO CALDERA 60 H70", 46, 70),
        ("ACC60D/I", "ALTO CALDERA 60 D/I H90", 51, 90),
        ("ACC60", "ALTO CALDERA 60 H90", 52, 90),
    ]
    for item in alto_caldera:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO CALDERA", t1, height=h))

    # ALTO CALENTADOR
    alto_calentador = [
        ("ACA45D/I", "ALTO CALENTADOR 45 D/I H70", 36, 70),
        ("ACA60D/I", "ALTO CALENTADOR 60 D/I H70", 37, 70),
        ("ACA45D/I", "ALTO CALENTADOR 45 D/I H90", 40, 90),
        ("ACA60D/I", "ALTO CALENTADOR 60 D/I H90", 41, 90),
    ]
    for item in alto_calentador:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO CALENTADOR", t1, height=h))

    # ALTO MICROONDAS
    alto_microondas = [
        ("AM60D/I", "ALTO MICROONDAS 60 D/I H70", 40, 70),
        ("AM60", "ALTO MICROONDAS 60 H70", 47, 70),
        ("AMF60D/I", "ALTO MICROONDAS FRIGO 60 D/I H70", 52, 70),
        ("AMF60", "ALTO MICROONDAS FRIGO 60 H90", 54, 90),
    ]
    for item in alto_microondas:
        code, name, t1, h = item
        products_to_insert.append(create_product(code, name, "ALTO MICROONDAS", t1, height=h))

    # ALTO ESCURREPLATOS - H70 y H90
    alto_escurreplatos_h70 = [
        ("AE45D/I", "ALTO ESCURREPLATOS 45 D/I H70", 50),
        ("AE50D/I", "ALTO ESCURREPLATOS 50 D/I H70", 53),
        ("AE60D/I", "ALTO ESCURREPLATOS 60 D/I H70", 53),
        ("AE60", "ALTO ESCURREPLATOS 60 H70", 61),
        ("AE70", "ALTO ESCURREPLATOS 70 H70", 67),
        ("AE80", "ALTO ESCURREPLATOS 80 H70", 80),
        ("AE90", "ALTO ESCURREPLATOS 90 H70", 131),
    ]
    for code, name, t1 in alto_escurreplatos_h70:
        products_to_insert.append(create_product(code, name, "ALTO ESCURREPLATOS", t1, height=70))

    alto_escurreplatos_h90 = [
        ("AE45D/I", "ALTO ESCURREPLATOS 45 D/I H90", 65),
        ("AE50D/I", "ALTO ESCURREPLATOS 50 D/I H90", 67),
        ("AE60D/I", "ALTO ESCURREPLATOS 60 D/I H90", 76),
        ("AE60", "ALTO ESCURREPLATOS 60 H90", 77),
        ("AE70", "ALTO ESCURREPLATOS 70 H90", 88),
        ("AE80", "ALTO ESCURREPLATOS 80 H90", 146),
    ]
    for code, name, t1 in alto_escurreplatos_h90:
        products_to_insert.append(create_product(code, name, "ALTO ESCURREPLATOS", t1, height=90))

    # ALTO VITRINA - H70 y H90
    alto_vitrina_h70 = [
        ("AV30D/I", "ALTO VITRINA 30 D/I H70", 68),
        ("AV35D/I", "ALTO VITRINA 35 D/I H70", 72),
        ("AV40D/I", "ALTO VITRINA 40 D/I H70", 78),
        ("AV45D/I", "ALTO VITRINA 45 D/I H70", 80),
        ("AV50D/I", "ALTO VITRINA 50 D/I H70", 86),
        ("AV60D/I", "ALTO VITRINA 60 D/I H70", 110),
        ("AV60", "ALTO VITRINA 60 H70", 116),
        ("AV70", "ALTO VITRINA 70 H70", 125),
        ("AV80", "ALTO VITRINA 80 H70", 125),
        ("AV90", "ALTO VITRINA 90 H70", 131),
        ("AV100", "ALTO VITRINA 100 H70", 131),
    ]
    for code, name, t1 in alto_vitrina_h70:
        products_to_insert.append(create_product(code, name, "ALTO VITRINA", t1, height=70))

    alto_vitrina_h90 = [
        ("AV30D/I", "ALTO VITRINA 30 D/I H90", 83),
        ("AV35D/I", "ALTO VITRINA 35 D/I H90", 86),
        ("AV40D/I", "ALTO VITRINA 40 D/I H90", 96),
        ("AV45D/I", "ALTO VITRINA 45 D/I H90", 128),
        ("AV50D/I", "ALTO VITRINA 50 D/I H90", 135),
        ("AV60D/I", "ALTO VITRINA 60 D/I H90", 141),
        ("AV60", "ALTO VITRINA 60 H90", 145),
        ("AV70", "ALTO VITRINA 70 H90", 146),
    ]
    for code, name, t1 in alto_vitrina_h90:
        products_to_insert.append(create_product(code, name, "ALTO VITRINA", t1, height=90))

    # ==================== PÁGINA 4 - ALTO ABATIBLE, COMBINADO, etc. ====================
    # ALTO ABATIBLE - H70 y H90
    alto_abatible_h70 = [
        ("AA45", "ALTO ABATIBLE 45 H70", 95),
        ("AA60", "ALTO ABATIBLE 60 H70", 97),
        ("AA70", "ALTO ABATIBLE 70 H70", 106),
        ("AA80", "ALTO ABATIBLE 80 H70", 109),
        ("AA90", "ALTO ABATIBLE 90 H70", 110),
        ("AA100", "ALTO ABATIBLE 100 H70", 115),
    ]
    for code, name, t1 in alto_abatible_h70:
        products_to_insert.append(create_product(code, name, "ALTO ABATIBLE", t1, height=70))

    alto_abatible_h90 = [
        ("AA45", "ALTO ABATIBLE 45 H90", 99),
        ("AA60", "ALTO ABATIBLE 60 H90", 118),
        ("AA70", "ALTO ABATIBLE 70 H90", 121),
        ("AA80", "ALTO ABATIBLE 80 H90", 123),
        ("AA90", "ALTO ABATIBLE 90 H90", 125),
        ("AA100", "ALTO ABATIBLE 100 H90", 125),
    ]
    for code, name, t1 in alto_abatible_h90:
        products_to_insert.append(create_product(code, name, "ALTO ABATIBLE", t1, height=90))

    # ALTO COMBINADO PLUS - H70 y H90
    alto_combinado_plus_h70 = [
        ("ACP45", "ALTO COMBINADO PLUS 45 H70", 127),
        ("ACP50", "ALTO COMBINADO PLUS 50 H70", 129),
        ("ACP60", "ALTO COMBINADO PLUS 60 H70", 138),
        ("ACP70", "ALTO COMBINADO PLUS 70 H70", 141),
        ("ACP80", "ALTO COMBINADO PLUS 80 H70", 149),
        ("ACP90", "ALTO COMBINADO PLUS 90 H70", 158),
        ("ACP100", "ALTO COMBINADO PLUS 100 H70", 159),
    ]
    for code, name, t1 in alto_combinado_plus_h70:
        products_to_insert.append(create_product(code, name, "ALTO COMBINADO PLUS", t1, height=70))

    alto_combinado_plus_h90 = [
        ("ACP45", "ALTO COMBINADO PLUS 45 H90", 134),
        ("ACP50", "ALTO COMBINADO PLUS 50 H90", 131),
        ("ACP60", "ALTO COMBINADO PLUS 60 H90", 145),
        ("ACP70", "ALTO COMBINADO PLUS 70 H90", 146),
        ("ACP80", "ALTO COMBINADO PLUS 80 H90", 160),
        ("ACP90", "ALTO COMBINADO PLUS 90 H90", 172),
        ("ACP100", "ALTO COMBINADO PLUS 100 H90", 185),
    ]
    for code, name, t1 in alto_combinado_plus_h90:
        products_to_insert.append(create_product(code, name, "ALTO COMBINADO PLUS", t1, height=90))

    # ALTILLO - H70 y H90
    altillo_h70 = [
        ("L30", "ALTILLO 30 H70", 65),
        ("L35", "ALTILLO 35 H70", 66),
        ("L40", "ALTILLO 40 H70", 66),
        ("L45", "ALTILLO 45 H70", 66),
        ("L50", "ALTILLO 50 H70", 68),
        ("L60", "ALTILLO 60 H70", 69),
        ("L70", "ALTILLO 70 H70", 71),
        ("L80", "ALTILLO 80 H70", 73),
        ("L90", "ALTILLO 90 H70", 75),
        ("L100", "ALTILLO 100 H70", 80),
    ]
    for code, name, t1 in altillo_h70:
        products_to_insert.append(create_product(code, name, "ALTILLO", t1, height=70))

    altillo_h90 = [
        ("L30", "ALTILLO 30 H90", 70),
        ("L35", "ALTILLO 35 H90", 70),
        ("L40", "ALTILLO 40 H90", 70),
        ("L45", "ALTILLO 45 H90", 72),
        ("L50", "ALTILLO 50 H90", 73),
        ("L60", "ALTILLO 60 H90", 80),
        ("L70", "ALTILLO 70 H90", 82),
        ("L80", "ALTILLO 80 H90", 84),
        ("L90", "ALTILLO 90 H90", 88),
    ]
    for code, name, t1 in altillo_h90:
        products_to_insert.append(create_product(code, name, "ALTILLO", t1, height=90))

    # ALTILLO VITRINA
    altillo_vitrina = [
        ("LV35", "ALTILLO VITRINA 35", 88), ("LV40", "ALTILLO VITRINA 40", 93),
        ("LV45", "ALTILLO VITRINA 45", 92), ("LV50", "ALTILLO VITRINA 50", 101),
        ("LV55", "ALTILLO VITRINA 55", 103), ("LV60", "ALTILLO VITRINA 60", 105),
        ("LV70", "ALTILLO VITRINA 70", 110), ("LV80", "ALTILLO VITRINA 80", 116),
        ("LV90", "ALTILLO VITRINA 90", 118), ("LV100", "ALTILLO VITRINA 100", 126),
    ]
    for code, name, t1 in altillo_vitrina:
        products_to_insert.append(create_product(code, name, "ALTILLO VITRINA", t1))

    # SOBREENCIMERA - 127 y 147
    sobreencimera_127 = [
        ("S30D/I", "SOBREENCIMERA 30 D/I H127", 51),
        ("S35D/I", "SOBREENCIMERA 35 D/I H127", 52),
        ("S40D/I", "SOBREENCIMERA 40 D/I H127", 54),
        ("S45D/I", "SOBREENCIMERA 45 D/I H127", 56),
        ("S50D/I", "SOBREENCIMERA 50 D/I H127", 57),
        ("S60D/I", "SOBREENCIMERA 60 D/I H127", 60),
        ("S60", "SOBREENCIMERA 60 H127", 71),
    ]
    for code, name, t1 in sobreencimera_127:
        products_to_insert.append(create_product(code, name, "SOBREENCIMERA", t1, height=127))

    sobreencimera_147 = [
        ("S30D/I", "SOBREENCIMERA 30 D/I H147", 54),
        ("S35D/I", "SOBREENCIMERA 35 D/I H147", 56),
        ("S40D/I", "SOBREENCIMERA 40 D/I H147", 58),
        ("S45D/I", "SOBREENCIMERA 45 D/I H147", 59),
        ("S50D/I", "SOBREENCIMERA 50 D/I H147", 62),
        ("S60D/I", "SOBREENCIMERA 60 D/I H147", 65),
        ("S60", "SOBREENCIMERA 60 H147", 77),
    ]
    for code, name, t1 in sobreencimera_147:
        products_to_insert.append(create_product(code, name, "SOBREENCIMERA", t1, height=147))

    # SOBREENCIMERA CAJON
    sobreenc_cajon = [
        ("SC30D/I", "SOBREENCIMERA CAJON 30 D/I", 72),
        ("SC35D/I", "SOBREENCIMERA CAJON 35 D/I", 74),
        ("SC40D/I", "SOBREENCIMERA CAJON 40 D/I", 76),
        ("SC45D/I", "SOBREENCIMERA CAJON 45 D/I", 78),
        ("SC50D/I", "SOBREENCIMERA CAJON 50 D/I", 80),
        ("SC60D/I", "SOBREENCIMERA CAJON 60 D/I", 83),
        ("SC60", "SOBREENCIMERA CAJON 60", 94),
    ]
    for code, name, t1 in sobreenc_cajon:
        products_to_insert.append(create_product(code, name, "SOBREENCIMERA CAJON", t1))

    # SOBREENCIMERA VITRINA
    sobreenc_vitrina = [
        ("SV30D/I", "SOBREENCIMERA VITRINA 30 D/I", 122),
        ("SV35D/I", "SOBREENCIMERA VITRINA 35 D/I", 128),
        ("SV40D/I", "SOBREENCIMERA VITRINA 40 D/I", 132),
        ("SV45D/I", "SOBREENCIMERA VITRINA 45 D/I", 137),
        ("SV50D/I", "SOBREENCIMERA VITRINA 50 D/I", 143),
        ("SV60D/I", "SOBREENCIMERA VITRINA 60 D/I", 149),
        ("SV60", "SOBREENCIMERA VITRINA 60", 170),
    ]
    for code, name, t1 in sobreenc_vitrina:
        products_to_insert.append(create_product(code, name, "SOBREENCIMERA VITRINA", t1))

    # SOBREENCIMERA VITRINA CAJON
    sobreenc_vit_cajon = [
        ("SVC30D/I", "SOBREENCIMERA VITRINA CAJON 30 D/I", 149),
        ("SVC35D/I", "SOBREENCIMERA VITRINA CAJON 35 D/I", 155),
        ("SVC40D/I", "SOBREENCIMERA VITRINA CAJON 40 D/I", 178),
        ("SVC45D/I", "SOBREENCIMERA VITRINA CAJON 45 D/I", 185),
        ("SVC50D/I", "SOBREENCIMERA VITRINA CAJON 50 D/I", 203),
        ("SVC60D/I", "SOBREENCIMERA VITRINA CAJON 60 D/I", 223),
    ]
    for code, name, t1 in sobreenc_vit_cajon:
        products_to_insert.append(create_product(code, name, "SOBREENCIMERA VITRINA CAJON", t1))

    # ==================== PÁGINA 5 - COLUMNAS ====================
    # COLUMNA DESPENSERO/ESCOBERO - 200 y 220
    columna_despensero_200 = [
        ("CD30D/I", "COLUMNA DESPENSERO 30 D/I H200", 90),
        ("CD35D/I", "COLUMNA DESPENSERO 35 D/I H200", 91),
        ("CD40D/I", "COLUMNA DESPENSERO 40 D/I H200", 96),
        ("CD50D/I", "COLUMNA DESPENSERO 50 D/I H200", 99),
        ("CD60", "COLUMNA DESPENSERO 60 H200", 101),
        ("CD70", "COLUMNA DESPENSERO 70 H200", 103),
        ("CD80", "COLUMNA DESPENSERO 80 H200", 112),
        ("CD90", "COLUMNA DESPENSERO 90 H200", 132),
    ]
    for code, name, t1 in columna_despensero_200:
        products_to_insert.append(create_product(code, name, "COLUMNA DESPENSERO", t1, height=200))

    columna_despensero_220 = [
        ("CD30D/I", "COLUMNA DESPENSERO 30 D/I H220", 94),
        ("CD35D/I", "COLUMNA DESPENSERO 35 D/I H220", 97),
        ("CD40D/I", "COLUMNA DESPENSERO 40 D/I H220", 101),
        ("CD50D/I", "COLUMNA DESPENSERO 50 D/I H220", 103),
        ("CD60", "COLUMNA DESPENSERO 60 H220", 111),
        ("CD70", "COLUMNA DESPENSERO 70 H220", 117),
        ("CD80", "COLUMNA DESPENSERO 80 H220", 134),
        ("CD90", "COLUMNA DESPENSERO 90 H220", 151),
    ]
    for code, name, t1 in columna_despensero_220:
        products_to_insert.append(create_product(code, name, "COLUMNA DESPENSERO", t1, height=220))

    # COLUMNA FRIGO
    columna_frigo_200 = [
        ("CF60D/I", "COLUMNA FRIGO 60 D/I H200", 63),
        ("CF60", "COLUMNA FRIGO 60 H200", 73),
    ]
    for code, name, t1 in columna_frigo_200:
        products_to_insert.append(create_product(code, name, "COLUMNA FRIGO", t1, height=200))

    columna_frigo_220 = [
        ("CF60D/I", "COLUMNA FRIGO 60 D/I H220", 69),
        ("CF60", "COLUMNA FRIGO 60 H220", 79),
    ]
    for code, name, t1 in columna_frigo_220:
        products_to_insert.append(create_product(code, name, "COLUMNA FRIGO", t1, height=220))

    # MEDIACOLUMNA
    mediacolumna = [
        ("M30D/I", "MEDIACOLUMNA 30 D/I", 63),
        ("M35D/I", "MEDIACOLUMNA 35 D/I", 65),
        ("M40D/I", "MEDIACOLUMNA 40 D/I", 63),
        ("M45D/I", "MEDIACOLUMNA 45 D/I", 65),
        ("M50D/I", "MEDIACOLUMNA 50 D/I", 69),
        ("M60D/I", "MEDIACOLUMNA 60 D/I", 79),
        ("M60", "MEDIACOLUMNA 60", 93),
    ]
    for code, name, t1 in mediacolumna:
        products_to_insert.append(create_product(code, name, "MEDIACOLUMNA", t1))

    # MEDIACOLUMNA HORNO
    mediacolumna_horno = [
        ("MPH60D/I", "MEDIACOLUMNA HORNO 60 D/I", 130),
        ("MPH60", "MEDIACOLUMNA HORNO 60", 61),
        ("MPM60", "MEDIACOLUMNA HORNO MICRO 60", 68),
        ("MGHM60", "MEDIACOLUMNA HORNO MICRO GAVETA 60", 74),
        ("MCHM60", "MEDIACOLUMNA HORNO MICRO CAJON 60", 105),
    ]
    for code, name, t1 in mediacolumna_horno:
        products_to_insert.append(create_product(code, name, "MEDIACOLUMNA HORNO", t1))

    # MEDIA PUERTA GAVETA
    media_puerta_gaveta = [
        ("MPG30D/I", "MEDIA PUERTA GAVETA 30 D/I", 85),
        ("MPG35D/I", "MEDIA PUERTA GAVETA 35 D/I", 87),
        ("MPG40D/I", "MEDIA PUERTA GAVETA 40 D/I", 89),
        ("MPG45D/I", "MEDIA PUERTA GAVETA 45 D/I", 92),
        ("MPG50D/I", "MEDIA PUERTA GAVETA 50 D/I", 95),
        ("MPG60D/I", "MEDIA PUERTA GAVETA 60 D/I", 99),
        ("MPG60", "MEDIA PUERTA GAVETA 60", 130),
    ]
    for code, name, t1 in media_puerta_gaveta:
        products_to_insert.append(create_product(code, name, "MEDIA PUERTA GAVETA", t1))

    # MEDIACOLUMNA VITRINA
    mediacolumna_vitrina = [
        ("MV30D/I", "MEDIACOLUMNA VITRINA 30 D/I", 162),
        ("MV35D/I", "MEDIACOLUMNA VITRINA 35 D/I", 167),
        ("MV40D/I", "MEDIACOLUMNA VITRINA 40 D/I", 197),
        ("MV45D/I", "MEDIACOLUMNA VITRINA 45 D/I", 205),
        ("MV50D/I", "MEDIACOLUMNA VITRINA 50 D/I", 210),
        ("MV60D/I", "MEDIACOLUMNA VITRINA 60 D/I", 170),
        ("MV60", "MEDIACOLUMNA VITRINA 60", 190),
    ]
    for code, name, t1 in mediacolumna_vitrina:
        products_to_insert.append(create_product(code, name, "MEDIACOLUMNA VITRINA", t1))

    # MEDIACOL VITRINA GAVETA
    mediacol_vit_gaveta = [
        ("MVG30D/I", "MEDIACOL VITRINA GAVETA 30 D/I", 125),
        ("MVG35D/I", "MEDIACOL VITRINA GAVETA 35 D/I", 131),
        ("MVG40D/I", "MEDIACOL VITRINA GAVETA 40 D/I", 135),
        ("MVG45D/I", "MEDIACOL VITRINA GAVETA 45 D/I", 141),
        ("MVG50D/I", "MEDIACOL VITRINA GAVETA 50 D/I", 146),
        ("MVG60D/I", "MEDIACOL VITRINA GAVETA 60 D/I", 159),
        ("MVG60", "MEDIACOL VITRINA GAVETA 60", 170),
    ]
    for code, name, t1 in mediacol_vit_gaveta:
        products_to_insert.append(create_product(code, name, "MEDIACOL VITRINA GAVETA", t1))

    # COLUMNA HORNO - 200 y 220
    columna_horno_200 = [
        ("CH60D/I", "COLUMNA HORNO 60 D/I H200", 110),
        ("CH60", "COLUMNA HORNO 60 H200", 117),
        ("CHMC60D/I", "COLUMNA HORNO MICRO 60 D/I H200", 129),
        ("CHMC60", "COLUMNA HORNO MICRO 60 H200", 134),
        ("CHGC60D/I", "COLUMNA HORNO GAVETA CAJON 60 D/I H200", 167),
        ("CHGC60", "COLUMNA HORNO GAVETA CAJON 60 H200", 173),
        ("CHPC60D/I", "COLUMNA HORNO PUERTA CAJON 60 D/I H200", 181),
        ("CHPC60", "COLUMNA HORNO PUERTA CAJON 60 H200", 187),
    ]
    for code, name, t1 in columna_horno_200:
        products_to_insert.append(create_product(code, name, "COLUMNA HORNO", t1, height=200))

    columna_horno_220 = [
        ("CH60D/I", "COLUMNA HORNO 60 D/I H220", 134),
        ("CH60", "COLUMNA HORNO 60 H220", 151),
        ("CHMC60D/I", "COLUMNA HORNO MICRO 60 D/I H220", 143),
        ("CHMC60", "COLUMNA HORNO MICRO 60 H220", 156),
        ("CHGC60D/I", "COLUMNA HORNO GAVETA CAJON 60 D/I H220", 172),
        ("CHGC60", "COLUMNA HORNO GAVETA CAJON 60 H220", 234),
        ("CHPC60D/I", "COLUMNA HORNO PUERTA CAJON 60 D/I H220", 237),
        ("CHPC60", "COLUMNA HORNO PUERTA CAJON 60 H220", 246),
    ]
    for code, name, t1 in columna_horno_220:
        products_to_insert.append(create_product(code, name, "COLUMNA HORNO", t1, height=220))

    # BOTELLEROS
    botelleros = [
        ("BOA", "BOTELLERO 70/90x15x33", 41, 70, 15, 33),
        ("BOS", "BOTELLERO 127/147x15x33", 47, 127, 15, 33),
        ("BOC", "BOTELLERO 200/220x15x33", 60, 200, 15, 33),
    ]
    for item in botelleros:
        code, name, t1, h, w, d = item
        products_to_insert.append(create_product(code, name, "BOTELLEROS", t1, height=h, width=w, depth=d))

    # ALTILLOS DECORATIVOS
    altillos_decorativos = [
        ("LD30", "ALTILLO DECORATIVO 30", 23),
        ("LD35", "ALTILLO DECORATIVO 35", 24),
        ("LD40", "ALTILLO DECORATIVO 40", 25),
        ("LD45", "ALTILLO DECORATIVO 45", 26),
        ("LD50", "ALTILLO DECORATIVO 50", 27),
        ("LD60", "ALTILLO DECORATIVO 60", 29),
        ("LD70", "ALTILLO DECORATIVO 70", 30),
        ("LD80", "ALTILLO DECORATIVO 80", 33),
        ("LD90", "ALTILLO DECORATIVO 90", 34),
        ("LD100", "ALTILLO DECORATIVO 100", 36),
    ]
    for code, name, t1 in altillos_decorativos:
        products_to_insert.append(create_product(code, name, "ALTILLOS DECORATIVOS", t1))

    # Delete existing MV products first
    deleted = db.products.delete_many({"library": "MV"})
    print(f"Deleted {deleted.deleted_count} existing MV products")

    # Insert new products
    if products_to_insert:
        result = db.products.insert_many(products_to_insert)
        print(f"Inserted {len(result.inserted_ids)} MV products")

    # Show summary by category
    print("\n=== RESUMEN DE PRODUCTOS MV ===")
    categories = {}
    for p in products_to_insert:
        cat = p['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print(f"\n=== TOTAL: {len(products_to_insert)} productos MV ===")

if __name__ == "__main__":
    main()
