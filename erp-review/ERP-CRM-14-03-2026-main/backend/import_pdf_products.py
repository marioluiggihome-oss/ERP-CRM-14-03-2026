#!/usr/bin/env python3
"""
Script de importación de productos faltantes del catálogo PDF
Parte 3 y Parte 4 - TARIFA TÉCNICA ZONACOCINAS
"""
import json
from pymongo import MongoClient
from datetime import datetime

# Conectar a MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['luiggi_home']
products_collection = db['products']

# ===============================================
# PRODUCTOS PARTE 3 - ALTOS GOLA 45cm y más
# ===============================================

PRODUCTS_PART3 = [
    # ALTO GOLA 45cm - 1 puerta
    {"code": "G45A1P350", "name": "Alto gola 1 puerta (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 92, "Z2": 97, "Z3": 103, "Z4": 98, "Z5": 104, "Z6": 122, "Z7": 129, "Z8": 132, "Z9": 139, "Z10": 148, "Z11": 155, "Z12": 184}},
    {"code": "G45A1P400", "name": "Alto gola 1 puerta (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 97, "Z2": 102, "Z3": 108, "Z4": 104, "Z5": 111, "Z6": 126, "Z7": 134, "Z8": 137, "Z9": 143, "Z10": 154, "Z11": 162, "Z12": 190}},
    {"code": "G45A1P450", "name": "Alto gola 1 puerta (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 102, "Z2": 107, "Z3": 114, "Z4": 110, "Z5": 119, "Z6": 130, "Z7": 139, "Z8": 141, "Z9": 147, "Z10": 162, "Z11": 169, "Z12": 196}},
    {"code": "G45A1P500", "name": "Alto gola 1 puerta (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 107, "Z2": 112, "Z3": 121, "Z4": 117, "Z5": 126, "Z6": 135, "Z7": 144, "Z8": 146, "Z9": 153, "Z10": 168, "Z11": 175, "Z12": 203}},
    {"code": "G45A1P600", "name": "Alto gola 1 puerta (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 117, "Z2": 123, "Z3": 132, "Z4": 127, "Z5": 139, "Z6": 148, "Z7": 158, "Z8": 161, "Z9": 169, "Z10": 181, "Z11": 188, "Z12": 215}},
    
    # ALTO GOLA 45cm - 2 puertas
    {"code": "G45A2P600", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 141, "Z2": 148, "Z3": 160, "Z4": 152, "Z5": 166, "Z6": 202, "Z7": 217, "Z8": 222, "Z9": 233, "Z10": 250, "Z11": 265, "Z12": 320}},
    {"code": "G45A2P700", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 151, "Z2": 160, "Z3": 172, "Z4": 162, "Z5": 174, "Z6": 210, "Z7": 226, "Z8": 231, "Z9": 244, "Z10": 264, "Z11": 278, "Z12": 334}},
    {"code": "G45A2P800", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 161, "Z2": 169, "Z3": 184, "Z4": 174, "Z5": 189, "Z6": 218, "Z7": 235, "Z8": 239, "Z9": 252, "Z10": 276, "Z11": 291, "Z12": 347}},
    {"code": "G45A2P900", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 170, "Z2": 180, "Z3": 195, "Z4": 187, "Z5": 205, "Z6": 227, "Z7": 244, "Z8": 248, "Z9": 261, "Z10": 290, "Z11": 303, "Z12": 359}},
    {"code": "G45A2P1000", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 181, "Z2": 191, "Z3": 208, "Z4": 201, "Z5": 219, "Z6": 237, "Z7": 255, "Z8": 259, "Z9": 273, "Z10": 302, "Z11": 317, "Z12": 372}},
    {"code": "G45A2P1200", "name": "Alto gola 2 puertas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 200, "Z2": 212, "Z3": 232, "Z4": 222, "Z5": 244, "Z6": 263, "Z7": 282, "Z8": 288, "Z9": 303, "Z10": 329, "Z11": 342, "Z12": 397}},
    
    # ALTO GOLA 45cm - 1 Vitrina
    {"code": "G45A1V350", "name": "Alto gola 1 Vitrina (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 128, "Z2": 118, "Z3": 124, "Z4": 120, "Z5": 126, "Z6": 135, "Z7": 143, "Z8": 146, "Z9": 152, "Z10": 162, "Z11": 169, "Z12": 197}},
    {"code": "G45A1V400", "name": "Alto gola 1 Vitrina (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 134, "Z2": 125, "Z3": 132, "Z4": 128, "Z5": 135, "Z6": 142, "Z7": 150, "Z8": 152, "Z9": 159, "Z10": 170, "Z11": 177, "Z12": 206}},
    {"code": "G45A1V450", "name": "Alto gola 1 Vitrina (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 141, "Z2": 132, "Z3": 140, "Z4": 137, "Z5": 145, "Z6": 148, "Z7": 156, "Z8": 159, "Z9": 165, "Z10": 180, "Z11": 186, "Z12": 214}},
    {"code": "G45A1V500", "name": "Alto gola 1 Vitrina (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 147, "Z2": 140, "Z3": 148, "Z4": 145, "Z5": 154, "Z6": 154, "Z7": 164, "Z8": 166, "Z9": 173, "Z10": 188, "Z11": 195, "Z12": 223}},
    {"code": "G45A1V600", "name": "Alto gola 1 Vitrina (Derecha/Izquierda)", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 161, "Z2": 154, "Z3": 164, "Z4": 160, "Z5": 170, "Z6": 171, "Z7": 182, "Z8": 184, "Z9": 192, "Z10": 205, "Z11": 212, "Z12": 239}},
    
    # ALTO GOLA 45cm - 2 Vitrinas
    {"code": "G45A2V600", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 210, "Z2": 188, "Z3": 200, "Z4": 193, "Z5": 206, "Z6": 226, "Z7": 242, "Z8": 245, "Z9": 257, "Z10": 273, "Z11": 289, "Z12": 344}},
    {"code": "G45A2V700", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 223, "Z2": 203, "Z3": 215, "Z4": 206, "Z5": 219, "Z6": 237, "Z7": 253, "Z8": 258, "Z9": 271, "Z10": 291, "Z11": 306, "Z12": 361}},
    {"code": "G45A2V800", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 235, "Z2": 217, "Z3": 231, "Z4": 223, "Z5": 237, "Z6": 250, "Z7": 267, "Z8": 271, "Z9": 285, "Z10": 308, "Z11": 322, "Z12": 378}},
    {"code": "G45A2V900", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 249, "Z2": 231, "Z3": 247, "Z4": 239, "Z5": 256, "Z6": 261, "Z7": 279, "Z8": 284, "Z9": 296, "Z10": 324, "Z11": 339, "Z12": 394}},
    {"code": "G45A2V1000", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 261, "Z2": 247, "Z3": 264, "Z4": 256, "Z5": 276, "Z6": 276, "Z7": 294, "Z8": 298, "Z9": 313, "Z10": 342, "Z11": 356, "Z12": 412}},
    {"code": "G45A2V1200", "name": "Alto gola 2 Vitrinas", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 288, "Z2": 275, "Z3": 295, "Z4": 286, "Z5": 308, "Z6": 310, "Z7": 330, "Z8": 335, "Z9": 351, "Z10": 376, "Z11": 391, "Z12": 444}},
    
    # ALTO GOLA 45cm - Abatibles HK-TOP
    {"code": "G45APABL350", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 153, "Z2": 158, "Z3": 164, "Z4": 159, "Z5": 165, "Z6": 183, "Z7": 191, "Z8": 193, "Z9": 200, "Z10": 209, "Z11": 216, "Z12": 245}},
    {"code": "G45APABL400", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 159, "Z2": 163, "Z3": 170, "Z4": 165, "Z5": 172, "Z6": 187, "Z7": 195, "Z8": 197, "Z9": 205, "Z10": 216, "Z11": 224, "Z12": 251}},
    {"code": "G45APABL450", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 164, "Z2": 168, "Z3": 175, "Z4": 171, "Z5": 181, "Z6": 191, "Z7": 200, "Z8": 202, "Z9": 209, "Z10": 223, "Z11": 230, "Z12": 257}},
    {"code": "G45APABL500", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 168, "Z2": 173, "Z3": 182, "Z4": 177, "Z5": 188, "Z6": 196, "Z7": 205, "Z8": 208, "Z9": 214, "Z10": 229, "Z11": 236, "Z12": 264}},
    {"code": "G45APABL600", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 177, "Z2": 184, "Z3": 194, "Z4": 189, "Z5": 200, "Z6": 209, "Z7": 219, "Z8": 222, "Z9": 230, "Z10": 243, "Z11": 249, "Z12": 276}},
    {"code": "G45APABL700", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 187, "Z2": 202, "Z3": 215, "Z4": 203, "Z5": 216, "Z6": 215, "Z7": 226, "Z8": 235, "Z9": 244, "Z10": 261, "Z11": 271, "Z12": 307}},
    {"code": "G45APABL800", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 196, "Z2": 213, "Z3": 227, "Z4": 214, "Z5": 229, "Z6": 246, "Z7": 260, "Z8": 264, "Z9": 275, "Z10": 273, "Z11": 281, "Z12": 318}},
    {"code": "G45APABL900", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 206, "Z2": 224, "Z3": 238, "Z4": 231, "Z5": 249, "Z6": 251, "Z7": 266, "Z8": 269, "Z9": 280, "Z10": 289, "Z11": 297, "Z12": 333}},
    {"code": "G45APABL1000", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 226, "Z2": 231, "Z3": 248, "Z4": 253, "Z5": 274, "Z6": 294, "Z7": 314, "Z8": 318, "Z9": 334, "Z10": 332, "Z11": 338, "Z12": 382}},
    {"code": "G45APABL1200", "name": "Alto gola 1 puerta abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 320, "Z2": 327, "Z3": 342, "Z4": 348, "Z5": 370, "Z6": 389, "Z7": 408, "Z8": 414, "Z9": 429, "Z10": 427, "Z11": 434, "Z12": 478}},
    
    # ALTO GOLA 45cm - Vitrina abatible HK-TOP
    {"code": "G45AVABL350", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 189, "Z2": 180, "Z3": 186, "Z4": 181, "Z5": 188, "Z6": 196, "Z7": 205, "Z8": 207, "Z9": 213, "Z10": 224, "Z11": 231, "Z12": 258}},
    {"code": "G45AVABL400", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 196, "Z2": 187, "Z3": 193, "Z4": 189, "Z5": 197, "Z6": 203, "Z7": 211, "Z8": 213, "Z9": 221, "Z10": 232, "Z11": 239, "Z12": 267}},
    {"code": "G45AVABL450", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 203, "Z2": 194, "Z3": 202, "Z4": 197, "Z5": 207, "Z6": 209, "Z7": 217, "Z8": 219, "Z9": 227, "Z10": 240, "Z11": 248, "Z12": 275}},
    {"code": "G45AVABL500", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 209, "Z2": 202, "Z3": 210, "Z4": 206, "Z5": 215, "Z6": 216, "Z7": 225, "Z8": 227, "Z9": 234, "Z10": 249, "Z11": 256, "Z12": 284}},
    {"code": "G45AVABL600", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 222, "Z2": 215, "Z3": 226, "Z4": 221, "Z5": 232, "Z6": 233, "Z7": 243, "Z8": 246, "Z9": 253, "Z10": 266, "Z11": 273, "Z12": 300}},
    {"code": "G45AVABL700", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 235, "Z2": 237, "Z3": 250, "Z4": 239, "Z5": 252, "Z6": 243, "Z7": 253, "Z8": 263, "Z9": 272, "Z10": 290, "Z11": 299, "Z12": 335}},
    {"code": "G45AVABL800", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 248, "Z2": 252, "Z3": 267, "Z4": 254, "Z5": 269, "Z6": 277, "Z7": 292, "Z8": 295, "Z9": 307, "Z10": 305, "Z11": 314, "Z12": 350}},
    {"code": "G45AVABL900", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 261, "Z2": 267, "Z3": 282, "Z4": 275, "Z5": 293, "Z6": 287, "Z7": 301, "Z8": 305, "Z9": 316, "Z10": 324, "Z11": 333, "Z12": 369}},
    {"code": "G45APVBL1000", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 274, "Z2": 279, "Z3": 295, "Z4": 300, "Z5": 322, "Z6": 333, "Z7": 353, "Z8": 358, "Z9": 374, "Z10": 372, "Z11": 378, "Z12": 422}},
    {"code": "G45APVBL1200", "name": "Alto gola 1 vitrina abatible HK-TOP", "category": "ALTO GOLA", "series": "GOLA", "zone_prices": {"Z1": 385, "Z2": 382, "Z3": 398, "Z4": 403, "Z5": 425, "Z6": 436, "Z7": 456, "Z8": 461, "Z9": 477, "Z10": 475, "Z11": 481, "Z12": 525}},
]

# ===============================================
# PRODUCTOS PARTE 4 - COLUMNAS GOLA VERTICALES
# ===============================================

PRODUCTS_PART4 = [
    # COLUMNAS GOLA VERTICALES 240cm
    {"code": "GV24CH1G1CL1P600", "name": "Columna gola vertical horno 1 Cacerolero + 1 cajón Lux push incluidos + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 627, "Z2": 646, "Z3": 683, "Z4": 684, "Z5": 731, "Z6": 764, "Z7": 806, "Z8": 816, "Z9": 849, "Z10": 859, "Z11": 886, "Z12": 999}},
    {"code": "GV24CHM1P1P600", "name": "Columna gola vertical horno micro 1 puerta + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 380, "Z2": 390, "Z3": 418, "Z4": 414, "Z5": 448, "Z6": 455, "Z7": 482, "Z8": 489, "Z9": 511, "Z10": 524, "Z11": 541, "Z12": 610}},
    {"code": "GV24CHM1GB1P600", "name": "Columna gola vertical horno 1 Cacerolero Bax push incluido + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 443, "Z2": 456, "Z3": 481, "Z4": 486, "Z5": 520, "Z6": 542, "Z7": 572, "Z8": 580, "Z9": 603, "Z10": 608, "Z11": 625, "Z12": 703}},
    {"code": "GV24CHM1GL1P600", "name": "Columna gola vertical horno 1 Cacerolero Lux push incluido + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 485, "Z2": 498, "Z3": 524, "Z4": 529, "Z5": 561, "Z6": 583, "Z7": 614, "Z8": 621, "Z9": 644, "Z10": 649, "Z11": 666, "Z12": 744}},
    {"code": "GV24CHM1G1CB1P600", "name": "Columna gola vertical horno micro 1 Cacerolero + 1 cajón Bax push incluidos + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 537, "Z2": 553, "Z3": 585, "Z4": 586, "Z5": 625, "Z6": 637, "Z7": 670, "Z8": 677, "Z9": 704, "Z10": 748, "Z11": 775, "Z12": 879}},
    {"code": "GV24CHM1G1CL1P600", "name": "Columna gola vertical horno micro 1 Cacerolero + 1 cajón Lux push incluidos + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 618, "Z2": 635, "Z3": 665, "Z4": 666, "Z5": 705, "Z6": 717, "Z7": 750, "Z8": 759, "Z9": 784, "Z10": 828, "Z11": 855, "Z12": 960}},
    {"code": "GV24CHM2GB1P600", "name": "Columna gola vertical horno micro 2 Caceroleros Bax push incluidos + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 571, "Z2": 587, "Z3": 619, "Z4": 620, "Z5": 659, "Z6": 671, "Z7": 704, "Z8": 711, "Z9": 738, "Z10": 782, "Z11": 809, "Z12": 914}},
    {"code": "GV24CHM2GL1P600", "name": "Columna gola vertical horno micro 2 Caceroleros Lux push incluidos + 1 puerta", "category": "COLUMNA GOLA", "series": "GOLA", "zone_prices": {"Z1": 658, "Z2": 675, "Z3": 705, "Z4": 706, "Z5": 745, "Z6": 758, "Z7": 790, "Z8": 799, "Z9": 825, "Z10": 868, "Z11": 895, "Z12": 1000}},
]


def import_products(products_list: list, source_name: str):
    """Importa productos a la base de datos"""
    imported = 0
    updated = 0
    skipped = 0
    
    for product in products_list:
        code = product["code"]
        
        # Verificar si ya existe
        existing = products_collection.find_one({"code": code})
        
        if existing:
            # Actualizar si ya existe
            products_collection.update_one(
                {"code": code},
                {"$set": {
                    "name": product["name"],
                    "category": product["category"],
                    "series": product["series"],
                    "zone_prices": product["zone_prices"],
                    "source": source_name,
                    "updated_at": datetime.now().isoformat()
                }}
            )
            updated += 1
        else:
            # Insertar nuevo producto
            new_product = {
                "code": code,
                "name": product["name"],
                "category": product["category"],
                "series": product["series"],
                "zone_prices": product["zone_prices"],
                "source": source_name,
                "imported_at": datetime.now().isoformat(),
                "width": 0,
                "height": 0,
                "depth": 0
            }
            products_collection.insert_one(new_product)
            imported += 1
    
    return imported, updated, skipped


def main():
    print("=" * 60)
    print("IMPORTACIÓN DE PRODUCTOS - TARIFA TÉCNICA ZONACOCINAS")
    print("=" * 60)
    
    # Contar productos antes
    count_before = products_collection.count_documents({})
    print(f"\nProductos antes de la importación: {count_before}")
    
    # Importar Parte 3
    print("\n--- Importando Parte 3 (Altos Gola 45cm) ---")
    imp3, upd3, skip3 = import_products(PRODUCTS_PART3, "tarifa_tecnica_parte3")
    print(f"  Nuevos: {imp3}, Actualizados: {upd3}")
    
    # Importar Parte 4
    print("\n--- Importando Parte 4 (Columnas Gola Verticales) ---")
    imp4, upd4, skip4 = import_products(PRODUCTS_PART4, "tarifa_tecnica_parte4")
    print(f"  Nuevos: {imp4}, Actualizados: {upd4}")
    
    # Contar productos después
    count_after = products_collection.count_documents({})
    print(f"\n" + "=" * 60)
    print(f"Productos después de la importación: {count_after}")
    print(f"Nuevos productos añadidos: {count_after - count_before}")
    print("=" * 60)
    
    # Verificar los productos importados
    print("\n--- Verificación de productos G45 ---")
    g45_count = products_collection.count_documents({"code": {"$regex": "^G45", "$options": "i"}})
    print(f"  Productos G45: {g45_count}")
    
    print("\n--- Verificación de productos GV24 ---")
    gv24_count = products_collection.count_documents({"code": {"$regex": "^GV24", "$options": "i"}})
    print(f"  Productos GV24: {gv24_count}")


if __name__ == "__main__":
    main()
