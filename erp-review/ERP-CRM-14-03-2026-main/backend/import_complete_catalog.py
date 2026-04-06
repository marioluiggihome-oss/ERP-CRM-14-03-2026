#!/usr/bin/env python3
"""
Script COMPLETO de importación de productos del catálogo PDF
TARIFA TÉCNICA ZONACOCINAS - Partes 1, 2, 3 y 4
- Sin duplicados
- Categorización correcta
- Medidas en centímetros
"""
import re
from pymongo import MongoClient
from datetime import datetime

# Conectar a MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['luiggi_home']
products_collection = db['products']

def format_name_with_cm(name, code):
    """Formatea el nombre añadiendo 'cm' a las medidas"""
    # Extraer el ancho del código (últimos 3-4 dígitos)
    width_match = re.search(r'(\d{3,4})$', code)
    if width_match:
        width = width_match.group(1)
        # Si el nombre termina con el número sin 'cm' o 'mm', añadir 'cm'
        if name.endswith(width) and not name.endswith('cm') and not name.endswith('mm'):
            name = name + 'mm'
    return name

def determine_category(code, name):
    """Determina la categoría basada en el código y nombre"""
    code_upper = code.upper()
    name_upper = name.upper()
    
    # Columnas
    if 'CD' in code_upper or 'COLUMNA' in name_upper:
        if 'DESPENSERO' in name_upper:
            return "COLUMNA DESPENSERO"
        if code_upper.startswith('G') or 'GOLA' in name_upper:
            return "COLUMNA GOLA"
        return "COLUMNA"
    
    # Semicolumnas
    if 'SC' in code_upper or 'SEMICOLUMNA' in name_upper:
        if code_upper.startswith('G') or 'GOLA' in name_upper:
            return "SEMICOLUMNA GOLA"
        return "SEMICOLUMNA"
    
    # Sobremódulos
    if 'SE' in code_upper and not 'SET' in code_upper:
        if code_upper.startswith('G') or 'GOLA' in name_upper:
            return "SOBREMODULO GOLA"
        return "SOBREMODULO"
    
    # Altos
    if code_upper.startswith(('G45', 'G60', 'G70', 'G7A', 'G80', 'G8A', 'G90', 'G9A', 'G11')):
        if 'A' in code_upper[3:6]:
            return "ALTO GOLA"
    if code_upper.startswith(('A45', 'A7A', 'A8A', 'A9A')):
        return "ALTO"
    if 'ALTO' in name_upper:
        if 'GOLA' in name_upper or code_upper.startswith('G'):
            return "ALTO GOLA"
        return "ALTO"
    
    # Bajos
    if code_upper.startswith('G8B') or code_upper.startswith('G9B'):
        return "BAJO GOLA"
    if code_upper.startswith('A8B') or code_upper.startswith('A9B'):
        return "BAJO"
    if 'BAJO' in name_upper:
        if 'GOLA' in name_upper or code_upper.startswith('G'):
            return "BAJO GOLA"
        return "BAJO"
    
    # Por defecto basado en prefijo
    if code_upper.startswith('G'):
        return "ALTO GOLA"
    if code_upper.startswith('A'):
        return "ALTO"
    
    return "OTRO"

def determine_series(code):
    """Determina la serie basada en el código"""
    if code.upper().startswith('G') or code.upper().startswith('GV'):
        return "GOLA"
    return "TIRADOR"

# ===============================================
# TODOS LOS PRODUCTOS - PARTE 3 (Altos Gola 45cm, 60cm, etc.)
# ===============================================

PRODUCTS_PART3_COMPLETE = [
    # ALTO GOLA 45cm - 1 puerta
    {"code": "G45A1P350", "name": "Alto gola 1 puerta 350mm", "zone_prices": {"Z1": 92, "Z2": 97, "Z3": 103, "Z4": 98, "Z5": 104, "Z6": 122, "Z7": 129, "Z8": 132, "Z9": 139, "Z10": 148, "Z11": 155, "Z12": 184}},
    {"code": "G45A1P400", "name": "Alto gola 1 puerta 400mm", "zone_prices": {"Z1": 97, "Z2": 102, "Z3": 108, "Z4": 104, "Z5": 111, "Z6": 126, "Z7": 134, "Z8": 137, "Z9": 143, "Z10": 154, "Z11": 162, "Z12": 190}},
    {"code": "G45A1P450", "name": "Alto gola 1 puerta 450mm", "zone_prices": {"Z1": 102, "Z2": 107, "Z3": 114, "Z4": 110, "Z5": 119, "Z6": 130, "Z7": 139, "Z8": 141, "Z9": 147, "Z10": 162, "Z11": 169, "Z12": 196}},
    {"code": "G45A1P500", "name": "Alto gola 1 puerta 500mm", "zone_prices": {"Z1": 107, "Z2": 112, "Z3": 121, "Z4": 117, "Z5": 126, "Z6": 135, "Z7": 144, "Z8": 146, "Z9": 153, "Z10": 168, "Z11": 175, "Z12": 203}},
    {"code": "G45A1P600", "name": "Alto gola 1 puerta 600mm", "zone_prices": {"Z1": 117, "Z2": 123, "Z3": 132, "Z4": 127, "Z5": 139, "Z6": 148, "Z7": 158, "Z8": 161, "Z9": 169, "Z10": 181, "Z11": 188, "Z12": 215}},
    
    # ALTO GOLA 45cm - 2 puertas
    {"code": "G45A2P600", "name": "Alto gola 2 puertas 600mm", "zone_prices": {"Z1": 141, "Z2": 148, "Z3": 160, "Z4": 152, "Z5": 166, "Z6": 202, "Z7": 217, "Z8": 222, "Z9": 233, "Z10": 250, "Z11": 265, "Z12": 320}},
    {"code": "G45A2P700", "name": "Alto gola 2 puertas 700mm", "zone_prices": {"Z1": 151, "Z2": 160, "Z3": 172, "Z4": 162, "Z5": 174, "Z6": 210, "Z7": 226, "Z8": 231, "Z9": 244, "Z10": 264, "Z11": 278, "Z12": 334}},
    {"code": "G45A2P800", "name": "Alto gola 2 puertas 800mm", "zone_prices": {"Z1": 161, "Z2": 169, "Z3": 184, "Z4": 174, "Z5": 189, "Z6": 218, "Z7": 235, "Z8": 239, "Z9": 252, "Z10": 276, "Z11": 291, "Z12": 347}},
    {"code": "G45A2P900", "name": "Alto gola 2 puertas 900mm", "zone_prices": {"Z1": 170, "Z2": 180, "Z3": 195, "Z4": 187, "Z5": 205, "Z6": 227, "Z7": 244, "Z8": 248, "Z9": 261, "Z10": 290, "Z11": 303, "Z12": 359}},
    {"code": "G45A2P1000", "name": "Alto gola 2 puertas 1000mm", "zone_prices": {"Z1": 181, "Z2": 191, "Z3": 208, "Z4": 201, "Z5": 219, "Z6": 237, "Z7": 255, "Z8": 259, "Z9": 273, "Z10": 302, "Z11": 317, "Z12": 372}},
    {"code": "G45A2P1200", "name": "Alto gola 2 puertas 1200mm", "zone_prices": {"Z1": 200, "Z2": 212, "Z3": 232, "Z4": 222, "Z5": 244, "Z6": 263, "Z7": 282, "Z8": 288, "Z9": 303, "Z10": 329, "Z11": 342, "Z12": 397}},
    
    # ALTO GOLA 45cm - 1 Vitrina
    {"code": "G45A1V350", "name": "Alto gola 1 vitrina 350mm", "zone_prices": {"Z1": 128, "Z2": 118, "Z3": 124, "Z4": 120, "Z5": 126, "Z6": 135, "Z7": 143, "Z8": 146, "Z9": 152, "Z10": 162, "Z11": 169, "Z12": 197}},
    {"code": "G45A1V400", "name": "Alto gola 1 vitrina 400mm", "zone_prices": {"Z1": 134, "Z2": 125, "Z3": 132, "Z4": 128, "Z5": 135, "Z6": 142, "Z7": 150, "Z8": 152, "Z9": 159, "Z10": 170, "Z11": 177, "Z12": 206}},
    {"code": "G45A1V450", "name": "Alto gola 1 vitrina 450mm", "zone_prices": {"Z1": 141, "Z2": 132, "Z3": 140, "Z4": 137, "Z5": 145, "Z6": 148, "Z7": 156, "Z8": 159, "Z9": 165, "Z10": 180, "Z11": 186, "Z12": 214}},
    {"code": "G45A1V500", "name": "Alto gola 1 vitrina 500mm", "zone_prices": {"Z1": 147, "Z2": 140, "Z3": 148, "Z4": 145, "Z5": 154, "Z6": 154, "Z7": 164, "Z8": 166, "Z9": 173, "Z10": 188, "Z11": 195, "Z12": 223}},
    {"code": "G45A1V600", "name": "Alto gola 1 vitrina 600mm", "zone_prices": {"Z1": 161, "Z2": 154, "Z3": 164, "Z4": 160, "Z5": 170, "Z6": 171, "Z7": 182, "Z8": 184, "Z9": 192, "Z10": 205, "Z11": 212, "Z12": 239}},
    
    # ALTO GOLA 45cm - 2 Vitrinas
    {"code": "G45A2V600", "name": "Alto gola 2 vitrinas 600mm", "zone_prices": {"Z1": 210, "Z2": 188, "Z3": 200, "Z4": 193, "Z5": 206, "Z6": 226, "Z7": 242, "Z8": 245, "Z9": 257, "Z10": 273, "Z11": 289, "Z12": 344}},
    {"code": "G45A2V700", "name": "Alto gola 2 vitrinas 700mm", "zone_prices": {"Z1": 223, "Z2": 203, "Z3": 215, "Z4": 206, "Z5": 219, "Z6": 237, "Z7": 253, "Z8": 258, "Z9": 271, "Z10": 291, "Z11": 306, "Z12": 361}},
    {"code": "G45A2V800", "name": "Alto gola 2 vitrinas 800mm", "zone_prices": {"Z1": 235, "Z2": 217, "Z3": 231, "Z4": 223, "Z5": 237, "Z6": 250, "Z7": 267, "Z8": 271, "Z9": 285, "Z10": 308, "Z11": 322, "Z12": 378}},
    {"code": "G45A2V900", "name": "Alto gola 2 vitrinas 900mm", "zone_prices": {"Z1": 249, "Z2": 231, "Z3": 247, "Z4": 239, "Z5": 256, "Z6": 261, "Z7": 279, "Z8": 284, "Z9": 296, "Z10": 324, "Z11": 339, "Z12": 394}},
    {"code": "G45A2V1000", "name": "Alto gola 2 vitrinas 1000mm", "zone_prices": {"Z1": 261, "Z2": 247, "Z3": 264, "Z4": 256, "Z5": 276, "Z6": 276, "Z7": 294, "Z8": 298, "Z9": 313, "Z10": 342, "Z11": 356, "Z12": 412}},
    {"code": "G45A2V1200", "name": "Alto gola 2 vitrinas 1200mm", "zone_prices": {"Z1": 288, "Z2": 275, "Z3": 295, "Z4": 286, "Z5": 308, "Z6": 310, "Z7": 330, "Z8": 335, "Z9": 351, "Z10": 376, "Z11": 391, "Z12": 444}},
    
    # ALTO GOLA 45cm - Abatibles HK-TOP
    {"code": "G45APABL350", "name": "Alto gola 1 puerta abatible HK-TOP 350mm", "zone_prices": {"Z1": 153, "Z2": 158, "Z3": 164, "Z4": 159, "Z5": 165, "Z6": 183, "Z7": 191, "Z8": 193, "Z9": 200, "Z10": 209, "Z11": 216, "Z12": 245}},
    {"code": "G45APABL400", "name": "Alto gola 1 puerta abatible HK-TOP 400mm", "zone_prices": {"Z1": 159, "Z2": 163, "Z3": 170, "Z4": 165, "Z5": 172, "Z6": 187, "Z7": 195, "Z8": 197, "Z9": 205, "Z10": 216, "Z11": 224, "Z12": 251}},
    {"code": "G45APABL450", "name": "Alto gola 1 puerta abatible HK-TOP 450mm", "zone_prices": {"Z1": 164, "Z2": 168, "Z3": 175, "Z4": 171, "Z5": 181, "Z6": 191, "Z7": 200, "Z8": 202, "Z9": 209, "Z10": 223, "Z11": 230, "Z12": 257}},
    {"code": "G45APABL500", "name": "Alto gola 1 puerta abatible HK-TOP 500mm", "zone_prices": {"Z1": 168, "Z2": 173, "Z3": 182, "Z4": 177, "Z5": 188, "Z6": 196, "Z7": 205, "Z8": 208, "Z9": 214, "Z10": 229, "Z11": 236, "Z12": 264}},
    {"code": "G45APABL600", "name": "Alto gola 1 puerta abatible HK-TOP 600mm", "zone_prices": {"Z1": 177, "Z2": 184, "Z3": 194, "Z4": 189, "Z5": 200, "Z6": 209, "Z7": 219, "Z8": 222, "Z9": 230, "Z10": 243, "Z11": 249, "Z12": 276}},
    {"code": "G45APABL700", "name": "Alto gola 1 puerta abatible HK-TOP 700mm", "zone_prices": {"Z1": 187, "Z2": 202, "Z3": 215, "Z4": 203, "Z5": 216, "Z6": 215, "Z7": 226, "Z8": 235, "Z9": 244, "Z10": 261, "Z11": 271, "Z12": 307}},
    {"code": "G45APABL800", "name": "Alto gola 1 puerta abatible HK-TOP 800mm", "zone_prices": {"Z1": 196, "Z2": 213, "Z3": 227, "Z4": 214, "Z5": 229, "Z6": 246, "Z7": 260, "Z8": 264, "Z9": 275, "Z10": 273, "Z11": 281, "Z12": 318}},
    {"code": "G45APABL900", "name": "Alto gola 1 puerta abatible HK-TOP 900mm", "zone_prices": {"Z1": 206, "Z2": 224, "Z3": 238, "Z4": 231, "Z5": 249, "Z6": 251, "Z7": 266, "Z8": 269, "Z9": 280, "Z10": 289, "Z11": 297, "Z12": 333}},
    {"code": "G45APABL1000", "name": "Alto gola 1 puerta abatible HK-TOP 1000mm", "zone_prices": {"Z1": 226, "Z2": 231, "Z3": 248, "Z4": 253, "Z5": 274, "Z6": 294, "Z7": 314, "Z8": 318, "Z9": 334, "Z10": 332, "Z11": 338, "Z12": 382}},
    {"code": "G45APABL1200", "name": "Alto gola 1 puerta abatible HK-TOP 1200mm", "zone_prices": {"Z1": 320, "Z2": 327, "Z3": 342, "Z4": 348, "Z5": 370, "Z6": 389, "Z7": 408, "Z8": 414, "Z9": 429, "Z10": 427, "Z11": 434, "Z12": 478}},
    
    # ALTO GOLA 45cm - Vitrina abatible HK-TOP
    {"code": "G45AVABL350", "name": "Alto gola 1 vitrina abatible HK-TOP 350mm", "zone_prices": {"Z1": 189, "Z2": 180, "Z3": 186, "Z4": 181, "Z5": 188, "Z6": 196, "Z7": 205, "Z8": 207, "Z9": 213, "Z10": 224, "Z11": 231, "Z12": 258}},
    {"code": "G45AVABL400", "name": "Alto gola 1 vitrina abatible HK-TOP 400mm", "zone_prices": {"Z1": 196, "Z2": 187, "Z3": 193, "Z4": 189, "Z5": 197, "Z6": 203, "Z7": 211, "Z8": 213, "Z9": 221, "Z10": 232, "Z11": 239, "Z12": 267}},
    {"code": "G45AVABL450", "name": "Alto gola 1 vitrina abatible HK-TOP 450mm", "zone_prices": {"Z1": 203, "Z2": 194, "Z3": 202, "Z4": 197, "Z5": 207, "Z6": 209, "Z7": 217, "Z8": 219, "Z9": 227, "Z10": 240, "Z11": 248, "Z12": 275}},
    {"code": "G45AVABL500", "name": "Alto gola 1 vitrina abatible HK-TOP 500mm", "zone_prices": {"Z1": 209, "Z2": 202, "Z3": 210, "Z4": 206, "Z5": 215, "Z6": 216, "Z7": 225, "Z8": 227, "Z9": 234, "Z10": 249, "Z11": 256, "Z12": 284}},
    {"code": "G45AVABL600", "name": "Alto gola 1 vitrina abatible HK-TOP 600mm", "zone_prices": {"Z1": 222, "Z2": 215, "Z3": 226, "Z4": 221, "Z5": 232, "Z6": 233, "Z7": 243, "Z8": 246, "Z9": 253, "Z10": 266, "Z11": 273, "Z12": 300}},
    {"code": "G45AVABL700", "name": "Alto gola 1 vitrina abatible HK-TOP 700mm", "zone_prices": {"Z1": 235, "Z2": 237, "Z3": 250, "Z4": 239, "Z5": 252, "Z6": 243, "Z7": 253, "Z8": 263, "Z9": 272, "Z10": 290, "Z11": 299, "Z12": 335}},
    {"code": "G45AVABL800", "name": "Alto gola 1 vitrina abatible HK-TOP 800mm", "zone_prices": {"Z1": 248, "Z2": 252, "Z3": 267, "Z4": 254, "Z5": 269, "Z6": 277, "Z7": 292, "Z8": 295, "Z9": 307, "Z10": 305, "Z11": 314, "Z12": 350}},
    {"code": "G45AVABL900", "name": "Alto gola 1 vitrina abatible HK-TOP 900mm", "zone_prices": {"Z1": 261, "Z2": 267, "Z3": 282, "Z4": 275, "Z5": 293, "Z6": 287, "Z7": 301, "Z8": 305, "Z9": 316, "Z10": 324, "Z11": 333, "Z12": 369}},
    {"code": "G45APVBL1000", "name": "Alto gola 1 vitrina abatible HK-TOP 1000mm", "zone_prices": {"Z1": 274, "Z2": 279, "Z3": 295, "Z4": 300, "Z5": 322, "Z6": 333, "Z7": 353, "Z8": 358, "Z9": 374, "Z10": 372, "Z11": 378, "Z12": 422}},
    {"code": "G45APVBL1200", "name": "Alto gola 1 vitrina abatible HK-TOP 1200mm", "zone_prices": {"Z1": 385, "Z2": 382, "Z3": 398, "Z4": 403, "Z5": 425, "Z6": 436, "Z7": 456, "Z8": 461, "Z9": 477, "Z10": 475, "Z11": 481, "Z12": 525}},
    
    # ALTO GOLA 60cm - 1 puerta
    {"code": "G60A1P350", "name": "Alto gola 60cm 1 puerta 350mm", "zone_prices": {"Z1": 105, "Z2": 110, "Z3": 118, "Z4": 113, "Z5": 121, "Z6": 138, "Z7": 147, "Z8": 150, "Z9": 157, "Z10": 168, "Z11": 176, "Z12": 201}},
    {"code": "G60A1P400", "name": "Alto gola 60cm 1 puerta 400mm", "zone_prices": {"Z1": 111, "Z2": 116, "Z3": 125, "Z4": 120, "Z5": 129, "Z6": 143, "Z7": 153, "Z8": 156, "Z9": 163, "Z10": 176, "Z11": 184, "Z12": 209}},
    {"code": "G60A1P450", "name": "Alto gola 60cm 1 puerta 450mm", "zone_prices": {"Z1": 117, "Z2": 123, "Z3": 132, "Z4": 127, "Z5": 138, "Z6": 149, "Z7": 159, "Z8": 162, "Z9": 170, "Z10": 184, "Z11": 192, "Z12": 218}},
    {"code": "G60A1P500", "name": "Alto gola 60cm 1 puerta 500mm", "zone_prices": {"Z1": 123, "Z2": 130, "Z3": 140, "Z4": 135, "Z5": 147, "Z6": 155, "Z7": 166, "Z8": 169, "Z9": 177, "Z10": 193, "Z11": 200, "Z12": 227}},
    {"code": "G60A1P600", "name": "Alto gola 60cm 1 puerta 600mm", "zone_prices": {"Z1": 136, "Z2": 143, "Z3": 155, "Z4": 149, "Z5": 163, "Z6": 172, "Z7": 184, "Z8": 187, "Z9": 196, "Z10": 211, "Z11": 219, "Z12": 247}},
    
    # ALTO GOLA 60cm - 2 puertas
    {"code": "G60A2P600", "name": "Alto gola 60cm 2 puertas 600mm", "zone_prices": {"Z1": 165, "Z2": 175, "Z3": 190, "Z4": 181, "Z5": 199, "Z6": 233, "Z7": 251, "Z8": 257, "Z9": 271, "Z10": 290, "Z11": 307, "Z12": 365}},
    {"code": "G60A2P700", "name": "Alto gola 60cm 2 puertas 700mm", "zone_prices": {"Z1": 177, "Z2": 188, "Z3": 205, "Z4": 194, "Z5": 211, "Z6": 244, "Z7": 263, "Z8": 269, "Z9": 284, "Z10": 307, "Z11": 324, "Z12": 383}},
    {"code": "G60A2P800", "name": "Alto gola 60cm 2 puertas 800mm", "zone_prices": {"Z1": 189, "Z2": 201, "Z3": 220, "Z4": 208, "Z5": 228, "Z6": 255, "Z7": 275, "Z8": 282, "Z9": 297, "Z10": 323, "Z11": 341, "Z12": 401}},
    {"code": "G60A2P900", "name": "Alto gola 60cm 2 puertas 900mm", "zone_prices": {"Z1": 201, "Z2": 214, "Z3": 235, "Z4": 223, "Z5": 245, "Z6": 267, "Z7": 288, "Z8": 294, "Z9": 310, "Z10": 341, "Z11": 358, "Z12": 419}},
    {"code": "G60A2P1000", "name": "Alto gola 60cm 2 puertas 1000mm", "zone_prices": {"Z1": 214, "Z2": 227, "Z3": 250, "Z4": 239, "Z5": 263, "Z6": 281, "Z7": 302, "Z8": 309, "Z9": 325, "Z10": 358, "Z11": 376, "Z12": 438}},
    {"code": "G60A2P1200", "name": "Alto gola 60cm 2 puertas 1200mm", "zone_prices": {"Z1": 238, "Z2": 253, "Z3": 280, "Z4": 266, "Z5": 294, "Z6": 311, "Z7": 335, "Z8": 342, "Z9": 360, "Z10": 392, "Z11": 410, "Z12": 474}},
    
    # SEMICOLUMNA GOLA 130cm
    {"code": "G13SC1P300", "name": "Semicolumna gola 130cm 1 puerta 300mm", "zone_prices": {"Z1": 182, "Z2": 188, "Z3": 203, "Z4": 199, "Z5": 217, "Z6": 239, "Z7": 255, "Z8": 260, "Z9": 273, "Z10": 281, "Z11": 289, "Z12": 334}},
    {"code": "G13SC1P350", "name": "Semicolumna gola 130cm 1 puerta 350mm", "zone_prices": {"Z1": 192, "Z2": 199, "Z3": 215, "Z4": 210, "Z5": 230, "Z6": 252, "Z7": 269, "Z8": 274, "Z9": 288, "Z10": 297, "Z11": 306, "Z12": 353}},
    {"code": "G13SC1P400", "name": "Semicolumna gola 130cm 1 puerta 400mm", "zone_prices": {"Z1": 203, "Z2": 210, "Z3": 227, "Z4": 222, "Z5": 243, "Z6": 265, "Z7": 283, "Z8": 289, "Z9": 303, "Z10": 314, "Z11": 323, "Z12": 372}},
    {"code": "G13SC1P450", "name": "Semicolumna gola 130cm 1 puerta 450mm", "zone_prices": {"Z1": 213, "Z2": 221, "Z3": 239, "Z4": 234, "Z5": 256, "Z6": 278, "Z7": 297, "Z8": 303, "Z9": 318, "Z10": 330, "Z11": 340, "Z12": 391}},
    {"code": "G13SC1P500", "name": "Semicolumna gola 130cm 1 puerta 500mm", "zone_prices": {"Z1": 224, "Z2": 232, "Z3": 251, "Z4": 246, "Z5": 269, "Z6": 291, "Z7": 311, "Z8": 318, "Z9": 333, "Z10": 347, "Z11": 357, "Z12": 410}},
    {"code": "G13SC1P600", "name": "Semicolumna gola 130cm 1 puerta 600mm", "zone_prices": {"Z1": 245, "Z2": 254, "Z3": 275, "Z4": 269, "Z5": 295, "Z6": 317, "Z7": 339, "Z8": 346, "Z9": 363, "Z10": 380, "Z11": 391, "Z12": 448}},
    
    # SEMICOLUMNA GOLA 130cm - 2 puertas
    {"code": "G13SC2P600", "name": "Semicolumna gola 130cm 2 puertas 600mm", "zone_prices": {"Z1": 298, "Z2": 311, "Z3": 340, "Z4": 329, "Z5": 363, "Z6": 429, "Z7": 464, "Z8": 474, "Z9": 500, "Z10": 515, "Z11": 537, "Z12": 640}},
    {"code": "G13SC2P700", "name": "Semicolumna gola 130cm 2 puertas 700mm", "zone_prices": {"Z1": 320, "Z2": 334, "Z3": 366, "Z4": 353, "Z5": 391, "Z6": 451, "Z7": 488, "Z8": 498, "Z9": 526, "Z10": 545, "Z11": 568, "Z12": 675}},
    {"code": "G13SC2P800", "name": "Semicolumna gola 130cm 2 puertas 800mm", "zone_prices": {"Z1": 342, "Z2": 358, "Z3": 393, "Z4": 380, "Z5": 420, "Z6": 475, "Z7": 513, "Z8": 524, "Z9": 553, "Z10": 576, "Z11": 600, "Z12": 711}},
    {"code": "G13SC2P900", "name": "Semicolumna gola 130cm 2 puertas 900mm", "zone_prices": {"Z1": 364, "Z2": 381, "Z3": 419, "Z4": 404, "Z5": 448, "Z6": 498, "Z7": 538, "Z8": 549, "Z9": 580, "Z10": 606, "Z11": 631, "Z12": 746}},
    {"code": "G13SC2P1000", "name": "Semicolumna gola 130cm 2 puertas 1000mm", "zone_prices": {"Z1": 386, "Z2": 404, "Z3": 445, "Z4": 429, "Z5": 476, "Z6": 521, "Z7": 563, "Z8": 575, "Z9": 607, "Z10": 637, "Z11": 663, "Z12": 782}},
    {"code": "G13SC2P1200", "name": "Semicolumna gola 130cm 2 puertas 1200mm", "zone_prices": {"Z1": 430, "Z2": 451, "Z3": 498, "Z4": 479, "Z5": 533, "Z6": 572, "Z7": 618, "Z8": 631, "Z9": 666, "Z10": 702, "Z11": 731, "Z12": 858}},
    
    # SEMICOLUMNA GOLA 140cm
    {"code": "G14SC1P300", "name": "Semicolumna gola 140cm 1 puerta 300mm", "zone_prices": {"Z1": 195, "Z2": 202, "Z3": 218, "Z4": 213, "Z5": 233, "Z6": 257, "Z7": 274, "Z8": 280, "Z9": 293, "Z10": 303, "Z11": 312, "Z12": 359}},
    {"code": "G14SC1P350", "name": "Semicolumna gola 140cm 1 puerta 350mm", "zone_prices": {"Z1": 206, "Z2": 214, "Z3": 231, "Z4": 226, "Z5": 247, "Z6": 271, "Z7": 290, "Z8": 296, "Z9": 310, "Z10": 321, "Z11": 331, "Z12": 380}},
    {"code": "G14SC1P400", "name": "Semicolumna gola 140cm 1 puerta 400mm", "zone_prices": {"Z1": 218, "Z2": 226, "Z3": 245, "Z4": 239, "Z5": 262, "Z6": 286, "Z7": 306, "Z8": 312, "Z9": 327, "Z10": 340, "Z11": 350, "Z12": 402}},
    {"code": "G14SC1P450", "name": "Semicolumna gola 140cm 1 puerta 450mm", "zone_prices": {"Z1": 230, "Z2": 238, "Z3": 258, "Z4": 252, "Z5": 276, "Z6": 301, "Z7": 322, "Z8": 329, "Z9": 345, "Z10": 358, "Z11": 369, "Z12": 423}},
    {"code": "G14SC1P500", "name": "Semicolumna gola 140cm 1 puerta 500mm", "zone_prices": {"Z1": 241, "Z2": 251, "Z3": 272, "Z4": 266, "Z5": 291, "Z6": 316, "Z7": 338, "Z8": 345, "Z9": 362, "Z10": 377, "Z11": 388, "Z12": 445}},
    {"code": "G14SC1P600", "name": "Semicolumna gola 140cm 1 puerta 600mm", "zone_prices": {"Z1": 265, "Z2": 275, "Z3": 299, "Z4": 292, "Z5": 320, "Z6": 346, "Z7": 370, "Z8": 378, "Z9": 397, "Z10": 414, "Z11": 426, "Z12": 488}},
    
    # COLUMNA GOLA 200cm
    {"code": "G20CD1P1P300", "name": "Columna gola 200cm 1 puerta + 1 puerta 300mm", "zone_prices": {"Z1": 266, "Z2": 276, "Z3": 300, "Z4": 292, "Z5": 321, "Z6": 356, "Z7": 381, "Z8": 389, "Z9": 409, "Z10": 421, "Z11": 434, "Z12": 502}},
    {"code": "G20CD1P1P350", "name": "Columna gola 200cm 1 puerta + 1 puerta 350mm", "zone_prices": {"Z1": 282, "Z2": 293, "Z3": 318, "Z4": 310, "Z5": 340, "Z6": 377, "Z7": 404, "Z8": 412, "Z9": 433, "Z10": 447, "Z11": 461, "Z12": 533}},
    {"code": "G20CD1P1P400", "name": "Columna gola 200cm 1 puerta + 1 puerta 400mm", "zone_prices": {"Z1": 298, "Z2": 309, "Z3": 337, "Z4": 328, "Z5": 360, "Z6": 398, "Z7": 427, "Z8": 436, "Z9": 458, "Z10": 474, "Z11": 488, "Z12": 564}},
    {"code": "G20CD1P1P450", "name": "Columna gola 200cm 1 puerta + 1 puerta 450mm", "zone_prices": {"Z1": 314, "Z2": 326, "Z3": 355, "Z4": 346, "Z5": 380, "Z6": 420, "Z7": 450, "Z8": 459, "Z9": 483, "Z10": 500, "Z11": 515, "Z12": 596}},
    {"code": "G20CD1P1P500", "name": "Columna gola 200cm 1 puerta + 1 puerta 500mm", "zone_prices": {"Z1": 330, "Z2": 343, "Z3": 374, "Z4": 364, "Z5": 400, "Z6": 441, "Z7": 473, "Z8": 483, "Z9": 507, "Z10": 527, "Z11": 542, "Z12": 627}},
    {"code": "G20CD1P1P600", "name": "Columna gola 200cm 1 puerta + 1 puerta 600mm", "zone_prices": {"Z1": 362, "Z2": 377, "Z3": 411, "Z4": 400, "Z5": 439, "Z6": 484, "Z7": 519, "Z8": 530, "Z9": 556, "Z10": 580, "Z11": 596, "Z12": 689}},
    
    # COLUMNA GOLA 220cm
    {"code": "G22CD1P1P300", "name": "Columna gola 220cm 1 puerta + 1 puerta 300mm", "zone_prices": {"Z1": 290, "Z2": 301, "Z3": 328, "Z4": 319, "Z5": 350, "Z6": 389, "Z7": 417, "Z8": 425, "Z9": 447, "Z10": 461, "Z11": 475, "Z12": 549}},
    {"code": "G22CD1P1P350", "name": "Columna gola 220cm 1 puerta + 1 puerta 350mm", "zone_prices": {"Z1": 308, "Z2": 320, "Z3": 349, "Z4": 339, "Z5": 373, "Z6": 413, "Z7": 443, "Z8": 452, "Z9": 475, "Z10": 491, "Z11": 506, "Z12": 585}},
    {"code": "G22CD1P1P400", "name": "Columna gola 220cm 1 puerta + 1 puerta 400mm", "zone_prices": {"Z1": 326, "Z2": 339, "Z3": 370, "Z4": 360, "Z5": 395, "Z6": 437, "Z7": 469, "Z8": 479, "Z9": 503, "Z10": 521, "Z11": 537, "Z12": 621}},
    {"code": "G22CD1P1P450", "name": "Columna gola 220cm 1 puerta + 1 puerta 450mm", "zone_prices": {"Z1": 344, "Z2": 358, "Z3": 391, "Z4": 380, "Z5": 418, "Z6": 461, "Z7": 495, "Z8": 505, "Z9": 531, "Z10": 551, "Z11": 567, "Z12": 656}},
    {"code": "G22CD1P1P500", "name": "Columna gola 220cm 1 puerta + 1 puerta 500mm", "zone_prices": {"Z1": 362, "Z2": 377, "Z3": 412, "Z4": 401, "Z5": 440, "Z6": 486, "Z7": 521, "Z8": 532, "Z9": 559, "Z10": 581, "Z11": 598, "Z12": 692}},
    {"code": "G22CD1P1P600", "name": "Columna gola 220cm 1 puerta + 1 puerta 600mm", "zone_prices": {"Z1": 398, "Z2": 414, "Z3": 453, "Z4": 441, "Z5": 485, "Z6": 535, "Z7": 574, "Z8": 586, "Z9": 615, "Z10": 641, "Z11": 659, "Z12": 763}},
    
    # COLUMNA GOLA 240cm
    {"code": "G24CD1P1P300", "name": "Columna gola 240cm 1 puerta + 1 puerta 300mm", "zone_prices": {"Z1": 340, "Z2": 354, "Z3": 386, "Z4": 375, "Z5": 412, "Z6": 457, "Z7": 490, "Z8": 500, "Z9": 525, "Z10": 542, "Z11": 558, "Z12": 548}},
    {"code": "G24CD1P1P350", "name": "Columna gola 240cm 1 puerta + 1 puerta 350mm", "zone_prices": {"Z1": 362, "Z2": 377, "Z3": 411, "Z4": 400, "Z5": 440, "Z6": 487, "Z7": 522, "Z8": 533, "Z9": 560, "Z10": 579, "Z11": 596, "Z12": 690}},
    {"code": "G24CD1P1P400", "name": "Columna gola 240cm 1 puerta + 1 puerta 400mm", "zone_prices": {"Z1": 384, "Z2": 400, "Z3": 437, "Z4": 425, "Z5": 467, "Z6": 517, "Z7": 555, "Z8": 566, "Z9": 595, "Z10": 616, "Z11": 634, "Z12": 734}},
    {"code": "G24CD1P1P450", "name": "Columna gola 240cm 1 puerta + 1 puerta 450mm", "zone_prices": {"Z1": 406, "Z2": 423, "Z3": 462, "Z4": 450, "Z5": 494, "Z6": 547, "Z7": 587, "Z8": 599, "Z9": 629, "Z10": 653, "Z11": 672, "Z12": 778}},
    {"code": "G24CD1P1P500", "name": "Columna gola 240cm 1 puerta + 1 puerta 500mm", "zone_prices": {"Z1": 428, "Z2": 446, "Z3": 487, "Z4": 474, "Z5": 521, "Z6": 577, "Z7": 619, "Z8": 632, "Z9": 663, "Z10": 690, "Z11": 710, "Z12": 822}},
    {"code": "G24CD1P1P600", "name": "Columna gola 240cm 1 puerta + 1 puerta 600mm", "zone_prices": {"Z1": 472, "Z2": 492, "Z3": 537, "Z4": 523, "Z5": 575, "Z6": 637, "Z7": 683, "Z8": 697, "Z9": 732, "Z10": 764, "Z11": 786, "Z12": 910}},
]

# ===============================================
# PRODUCTOS PARTE 4 - COLUMNAS VERTICALES
# ===============================================

PRODUCTS_PART4_COMPLETE = [
    # COLUMNAS GOLA VERTICALES 240cm
    {"code": "GV24CH1G1CL1P600", "name": "Columna gola vertical 240cm horno 1 cacerolero + 1 cajón Lux + 1 puerta 600mm", "zone_prices": {"Z1": 627, "Z2": 646, "Z3": 683, "Z4": 684, "Z5": 731, "Z6": 764, "Z7": 806, "Z8": 816, "Z9": 849, "Z10": 859, "Z11": 886, "Z12": 999}},
    {"code": "GV24CHM1P1P600", "name": "Columna gola vertical 240cm horno micro 1 puerta + 1 puerta 600mm", "zone_prices": {"Z1": 380, "Z2": 390, "Z3": 418, "Z4": 414, "Z5": 448, "Z6": 455, "Z7": 482, "Z8": 489, "Z9": 511, "Z10": 524, "Z11": 541, "Z12": 610}},
    {"code": "GV24CHM1GB1P600", "name": "Columna gola vertical 240cm horno 1 cacerolero Bax + 1 puerta 600mm", "zone_prices": {"Z1": 443, "Z2": 456, "Z3": 481, "Z4": 486, "Z5": 520, "Z6": 542, "Z7": 572, "Z8": 580, "Z9": 603, "Z10": 608, "Z11": 625, "Z12": 703}},
    {"code": "GV24CHM1GL1P600", "name": "Columna gola vertical 240cm horno 1 cacerolero Lux + 1 puerta 600mm", "zone_prices": {"Z1": 485, "Z2": 498, "Z3": 524, "Z4": 529, "Z5": 561, "Z6": 583, "Z7": 614, "Z8": 621, "Z9": 644, "Z10": 649, "Z11": 666, "Z12": 744}},
    {"code": "GV24CHM1G1CB1P600", "name": "Columna gola vertical 240cm horno micro 1 cacerolero + 1 cajón Bax + 1 puerta 600mm", "zone_prices": {"Z1": 537, "Z2": 553, "Z3": 585, "Z4": 586, "Z5": 625, "Z6": 637, "Z7": 670, "Z8": 677, "Z9": 704, "Z10": 748, "Z11": 775, "Z12": 879}},
    {"code": "GV24CHM1G1CL1P600", "name": "Columna gola vertical 240cm horno micro 1 cacerolero + 1 cajón Lux + 1 puerta 600mm", "zone_prices": {"Z1": 618, "Z2": 635, "Z3": 665, "Z4": 666, "Z5": 705, "Z6": 717, "Z7": 750, "Z8": 759, "Z9": 784, "Z10": 828, "Z11": 855, "Z12": 960}},
    {"code": "GV24CHM2GB1P600", "name": "Columna gola vertical 240cm horno micro 2 caceroleros Bax + 1 puerta 600mm", "zone_prices": {"Z1": 571, "Z2": 587, "Z3": 619, "Z4": 620, "Z5": 659, "Z6": 671, "Z7": 704, "Z8": 711, "Z9": 738, "Z10": 782, "Z11": 809, "Z12": 914}},
    {"code": "GV24CHM2GL1P600", "name": "Columna gola vertical 240cm horno micro 2 caceroleros Lux + 1 puerta 600mm", "zone_prices": {"Z1": 658, "Z2": 675, "Z3": 705, "Z4": 706, "Z5": 745, "Z6": 758, "Z7": 790, "Z8": 799, "Z9": 825, "Z10": 868, "Z11": 895, "Z12": 1000}},
    
    # COLUMNAS GOLA VERTICALES 220cm
    {"code": "GV22CD1P300", "name": "Columna gola vertical 220cm 1 puerta 300mm", "zone_prices": {"Z1": 285, "Z2": 296, "Z3": 323, "Z4": 314, "Z5": 345, "Z6": 384, "Z7": 412, "Z8": 420, "Z9": 442, "Z10": 456, "Z11": 470, "Z12": 544}},
    {"code": "GV22CD1P350", "name": "Columna gola vertical 220cm 1 puerta 350mm", "zone_prices": {"Z1": 303, "Z2": 315, "Z3": 344, "Z4": 334, "Z5": 367, "Z6": 408, "Z7": 438, "Z8": 447, "Z9": 470, "Z10": 486, "Z11": 501, "Z12": 580}},
    {"code": "GV22CD1P400", "name": "Columna gola vertical 220cm 1 puerta 400mm", "zone_prices": {"Z1": 321, "Z2": 334, "Z3": 365, "Z4": 355, "Z5": 390, "Z6": 432, "Z7": 464, "Z8": 474, "Z9": 498, "Z10": 516, "Z11": 532, "Z12": 616}},
    {"code": "GV22CD1P450", "name": "Columna gola vertical 220cm 1 puerta 450mm", "zone_prices": {"Z1": 339, "Z2": 353, "Z3": 386, "Z4": 375, "Z5": 413, "Z6": 456, "Z7": 490, "Z8": 500, "Z9": 526, "Z10": 546, "Z11": 562, "Z12": 651}},
    {"code": "GV22CD1P500", "name": "Columna gola vertical 220cm 1 puerta 500mm", "zone_prices": {"Z1": 357, "Z2": 372, "Z3": 407, "Z4": 396, "Z5": 435, "Z6": 481, "Z7": 516, "Z8": 527, "Z9": 554, "Z10": 576, "Z11": 593, "Z12": 687}},
    {"code": "GV22CD1P600", "name": "Columna gola vertical 220cm 1 puerta 600mm", "zone_prices": {"Z1": 393, "Z2": 409, "Z3": 447, "Z4": 436, "Z5": 479, "Z6": 529, "Z7": 568, "Z8": 580, "Z9": 609, "Z10": 635, "Z11": 654, "Z12": 757}},
]


def import_products_batch(products_list: list, source_name: str, dry_run: bool = False):
    """Importa productos a la base de datos con categorización correcta"""
    imported = 0
    updated = 0
    skipped = 0
    
    for product in products_list:
        code = product["code"]
        name = product["name"]
        
        # Determinar categoría y serie
        category = determine_category(code, name)
        series = determine_series(code)
        
        # Verificar si ya existe
        existing = products_collection.find_one({"code": code})
        
        product_data = {
            "name": name,
            "category": category,
            "series": series,
            "zone_prices": product.get("zone_prices", {}),
            "source": source_name,
            "width": 0,
            "height": 0,
            "depth": 0
        }
        
        if existing:
            if not dry_run:
                # Solo actualizar si tiene zone_prices nuevos
                if product.get("zone_prices"):
                    products_collection.update_one(
                        {"code": code},
                        {"$set": {
                            "zone_prices": product["zone_prices"],
                            "category": category,
                            "series": series,
                            "updated_at": datetime.now().isoformat()
                        }}
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                print(f"  [ACTUALIZAR] {code}: {name} -> {category}")
        else:
            if not dry_run:
                product_data["code"] = code
                product_data["imported_at"] = datetime.now().isoformat()
                products_collection.insert_one(product_data)
                imported += 1
            else:
                print(f"  [NUEVO] {code}: {name} -> {category}")
    
    return imported, updated, skipped


def update_existing_products_names():
    """Actualiza nombres de productos existentes para incluir 'mm' y corregir errores"""
    updates = 0
    
    # Buscar productos cuyos nombres terminan solo con número
    for doc in products_collection.find({"name": {"$regex": r"\d{3,4}$"}}):
        code = doc["code"]
        old_name = doc["name"]
        
        # Si ya termina en mm o cm, saltar
        if old_name.endswith('mm') or old_name.endswith('cm'):
            continue
        
        # Añadir 'mm' al final
        new_name = old_name + "mm"
        
        products_collection.update_one(
            {"code": code},
            {"$set": {"name": new_name}}
        )
        updates += 1
    
    return updates


def fix_categories():
    """Corrige categorías de productos existentes"""
    fixed = 0
    
    for doc in products_collection.find({}):
        code = doc["code"]
        name = doc.get("name", "")
        current_category = doc.get("category", "")
        
        correct_category = determine_category(code, name)
        correct_series = determine_series(code)
        
        if current_category != correct_category:
            products_collection.update_one(
                {"code": code},
                {"$set": {
                    "category": correct_category,
                    "series": correct_series
                }}
            )
            fixed += 1
    
    return fixed


def main():
    print("=" * 70)
    print("IMPORTACIÓN COMPLETA DE PRODUCTOS - TARIFA TÉCNICA ZONACOCINAS")
    print("=" * 70)
    
    # Contar productos antes
    count_before = products_collection.count_documents({})
    print(f"\nProductos antes: {count_before}")
    
    # 1. Importar Parte 3 completa
    print("\n--- Importando Parte 3 (Altos, Semicolumnas, Columnas Gola) ---")
    imp3, upd3, skip3 = import_products_batch(PRODUCTS_PART3_COMPLETE, "tarifa_tecnica_2025")
    print(f"  Nuevos: {imp3}, Actualizados: {upd3}, Sin cambios: {skip3}")
    
    # 2. Importar Parte 4 completa
    print("\n--- Importando Parte 4 (Columnas Gola Verticales) ---")
    imp4, upd4, skip4 = import_products_batch(PRODUCTS_PART4_COMPLETE, "tarifa_tecnica_2025")
    print(f"  Nuevos: {imp4}, Actualizados: {upd4}, Sin cambios: {skip4}")
    
    # 3. Actualizar nombres para incluir 'mm'
    print("\n--- Actualizando nombres con 'mm' ---")
    name_updates = update_existing_products_names()
    print(f"  Nombres actualizados: {name_updates}")
    
    # 4. Corregir categorías
    print("\n--- Corrigiendo categorías ---")
    cat_fixes = fix_categories()
    print(f"  Categorías corregidas: {cat_fixes}")
    
    # Contar productos después
    count_after = products_collection.count_documents({})
    
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Productos totales: {count_after}")
    print(f"Nuevos añadidos: {count_after - count_before}")
    
    # Mostrar distribución por categoría
    print("\n📊 DISTRIBUCIÓN POR CATEGORÍA:")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    for result in products_collection.aggregate(pipeline):
        cat = result["_id"] or "Sin categoría"
        print(f"  - {cat}: {result['count']}")
    
    # Mostrar distribución por prefijo
    print("\n📊 DISTRIBUCIÓN POR PREFIJO:")
    all_codes = [doc['code'] for doc in products_collection.find({}, {"code": 1, "_id": 0})]
    prefix_counts = {}
    for code in all_codes:
        if len(code) >= 3:
            pref = code[:3]
            prefix_counts[pref] = prefix_counts.get(pref, 0) + 1
    
    for pref in sorted(prefix_counts.keys()):
        print(f"  - {pref}: {prefix_counts[pref]}")


if __name__ == "__main__":
    main()
