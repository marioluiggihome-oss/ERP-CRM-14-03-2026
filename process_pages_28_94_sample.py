#!/usr/bin/env python3
"""
Script de importación masiva - Páginas 28-94 del catálogo TARIFA-COMPLETA.pdf
ALTOS 40cm, 45cm, 60cm, 70cm, 80cm, 90cm y SOBREMÓDULOS
Extraídos con análisis detallado de imágenes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'kitchen_budget')

# ========== PRODUCTOS EXTRAÍDOS DE PÁGINAS 28-94 ==========

PRODUCTS_PAGES_28_94 = [
    # ========== PÁGINA 28: ALTOS 40cm FONDO ESTÁNDAR ==========
    {"reference": "40A1P350", "name": "Alto 1 puerta 350mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 PUERTA", "height": 400, "depth": 330, "width": 350, "code": "40A1P350", "points": 72, "zonePoints": {"Z1": 72, "Z2": 77, "Z3": 83, "Z4": 77, "Z5": 84, "Z6": 102, "Z7": 109, "Z8": 112, "Z9": 119, "Z10": 128, "Z11": 135, "Z12": 164}, "page": 28},
    {"reference": "40A1P400", "name": "Alto 1 puerta 400mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 PUERTA", "height": 400, "depth": 330, "width": 400, "code": "40A1P400", "points": 77, "zonePoints": {"Z1": 77, "Z2": 81, "Z3": 88, "Z4": 83, "Z5": 90, "Z6": 105, "Z7": 113, "Z8": 116, "Z9": 122, "Z10": 134, "Z11": 142, "Z12": 169}, "page": 28},
    {"reference": "40A1P450", "name": "Alto 1 puerta 450mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 PUERTA", "height": 400, "depth": 330, "width": 450, "code": "40A1P450", "points": 81, "zonePoints": {"Z1": 81, "Z2": 85, "Z3": 93, "Z4": 89, "Z5": 98, "Z6": 108, "Z7": 118, "Z8": 119, "Z9": 126, "Z10": 140, "Z11": 147, "Z12": 174}, "page": 28},
    {"reference": "40A1P500", "name": "Alto 1 puerta 500mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 PUERTA", "height": 400, "depth": 330, "width": 500, "code": "40A1P500", "points": 85, "zonePoints": {"Z1": 85, "Z2": 90, "Z3": 99, "Z4": 95, "Z5": 104, "Z6": 113, "Z7": 122, "Z8": 124, "Z9": 131, "Z10": 146, "Z11": 153, "Z12": 181}, "page": 28},
    {"reference": "40A1P600", "name": "Alto 1 puerta 600mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 PUERTA", "height": 400, "depth": 330, "width": 600, "code": "40A1P600", "points": 89, "zonePoints": {"Z1": 89, "Z2": 95, "Z3": 103, "Z4": 101, "Z5": 111, "Z6": 121, "Z7": 131, "Z8": 133, "Z9": 141, "Z10": 145, "Z11": 153, "Z12": 184}, "page": 28},
    {"reference": "40A2P600", "name": "Alto 2 puertas 600mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 600, "code": "40A2P600", "points": 113, "zonePoints": {"Z1": 113, "Z2": 114, "Z3": 124, "Z4": 127, "Z5": 139, "Z6": 165, "Z7": 179, "Z8": 182, "Z9": 193, "Z10": 224, "Z11": 237, "Z12": 289}, "page": 28},
    {"reference": "40A2P700", "name": "Alto 2 puertas 700mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 700, "code": "40A2P700", "points": 126, "zonePoints": {"Z1": 126, "Z2": 134, "Z3": 147, "Z4": 137, "Z5": 150, "Z6": 185, "Z7": 201, "Z8": 206, "Z9": 218, "Z10": 238, "Z11": 253, "Z12": 309}, "page": 28},
    {"reference": "40A2P800", "name": "Alto 2 puertas 800mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 800, "code": "40A2P800", "points": 134, "zonePoints": {"Z1": 134, "Z2": 143, "Z3": 158, "Z4": 148, "Z5": 163, "Z6": 192, "Z7": 209, "Z8": 213, "Z9": 226, "Z10": 250, "Z11": 265, "Z12": 320}, "page": 28},
    {"reference": "40A2P900", "name": "Alto 2 puertas 900mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 900, "code": "40A2P900", "points": 143, "zonePoints": {"Z1": 143, "Z2": 152, "Z3": 168, "Z4": 160, "Z5": 176, "Z6": 198, "Z7": 216, "Z8": 221, "Z9": 233, "Z10": 261, "Z11": 276, "Z12": 331}, "page": 28},
    {"reference": "40A2P1000", "name": "Alto 2 puertas 1000mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 1000, "code": "40A2P1000", "points": 151, "zonePoints": {"Z1": 151, "Z2": 163, "Z3": 180, "Z4": 171, "Z5": 190, "Z6": 208, "Z7": 226, "Z8": 230, "Z9": 245, "Z10": 274, "Z11": 288, "Z12": 343}, "page": 28},
    {"reference": "40A2P1200", "name": "Alto 2 puertas 1200mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 PUERTAS", "height": 400, "depth": 330, "width": 1200, "code": "40A2P1200", "points": 160, "zonePoints": {"Z1": 160, "Z2": 171, "Z3": 189, "Z4": 184, "Z5": 205, "Z6": 225, "Z7": 244, "Z8": 248, "Z9": 264, "Z10": 272, "Z11": 289, "Z12": 349}, "page": 28},
    {"reference": "40A1V350", "name": "Alto 1 Vitrina 350mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 VITRINA", "height": 400, "depth": 330, "width": 350, "code": "40A1V350", "points": 105, "zonePoints": {"Z1": 105, "Z2": 97, "Z3": 103, "Z4": 98, "Z5": 105, "Z6": 113, "Z7": 122, "Z8": 124, "Z9": 130, "Z10": 141, "Z11": 148, "Z12": 175}, "page": 28},
    {"reference": "40A1V400", "name": "Alto 1 Vitrina 400mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 VITRINA", "height": 400, "depth": 330, "width": 400, "code": "40A1V400", "points": 109, "zonePoints": {"Z1": 109, "Z2": 103, "Z3": 110, "Z4": 105, "Z5": 113, "Z6": 120, "Z7": 128, "Z8": 130, "Z9": 137, "Z10": 148, "Z11": 155, "Z12": 183}, "page": 28},
    {"reference": "40A1V450", "name": "Alto 1 Vitrina 450mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 VITRINA", "height": 400, "depth": 330, "width": 450, "code": "40A1V450", "points": 116, "zonePoints": {"Z1": 116, "Z2": 109, "Z3": 117, "Z4": 113, "Z5": 122, "Z6": 124, "Z7": 133, "Z8": 135, "Z9": 142, "Z10": 155, "Z11": 163, "Z12": 190}, "page": 28},
    {"reference": "40A1V500", "name": "Alto 1 Vitrina 500mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 VITRINA", "height": 400, "depth": 330, "width": 500, "code": "40A1V500", "points": 122, "zonePoints": {"Z1": 122, "Z2": 116, "Z3": 124, "Z4": 121, "Z5": 130, "Z6": 130, "Z7": 140, "Z8": 142, "Z9": 149, "Z10": 164, "Z11": 170, "Z12": 198}, "page": 28},
    {"reference": "40A1V600", "name": "Alto 1 Vitrina 600mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 1 VITRINA", "height": 400, "depth": 330, "width": 600, "code": "40A1V600", "points": 132, "zonePoints": {"Z1": 132, "Z2": 124, "Z3": 132, "Z4": 130, "Z5": 141, "Z6": 142, "Z7": 152, "Z8": 154, "Z9": 162, "Z10": 166, "Z11": 174, "Z12": 205}, "page": 28},
    {"reference": "40A2V600", "name": "Alto 2 Vitrinas 600mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 600, "code": "40A2V600", "points": 180, "zonePoints": {"Z1": 180, "Z2": 151, "Z3": 161, "Z4": 165, "Z5": 176, "Z6": 186, "Z7": 200, "Z8": 203, "Z9": 214, "Z10": 245, "Z11": 258, "Z12": 310}, "page": 28},
    {"reference": "40A2V700", "name": "Alto 2 Vitrinas 700mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 700, "code": "40A2V700", "points": 191, "zonePoints": {"Z1": 191, "Z2": 175, "Z3": 188, "Z4": 177, "Z5": 191, "Z6": 209, "Z7": 226, "Z8": 230, "Z9": 244, "Z10": 263, "Z11": 277, "Z12": 333}, "page": 28},
    {"reference": "40A2V800", "name": "Alto 2 Vitrinas 800mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 800, "code": "40A2V800", "points": 201, "zonePoints": {"Z1": 201, "Z2": 187, "Z3": 202, "Z4": 192, "Z5": 208, "Z6": 221, "Z7": 234, "Z8": 242, "Z9": 254, "Z10": 278, "Z11": 293, "Z12": 348}, "page": 28},
    {"reference": "40A2V900", "name": "Alto 2 Vitrinas 900mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 900, "code": "40A2V900", "points": 213, "zonePoints": {"Z1": 213, "Z2": 200, "Z3": 215, "Z4": 208, "Z5": 226, "Z6": 230, "Z7": 248, "Z8": 252, "Z9": 265, "Z10": 293, "Z11": 308, "Z12": 362}, "page": 28},
    {"reference": "40A2V1000", "name": "Alto 2 Vitrinas 1000mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 1000, "code": "40A2V1000", "points": 225, "zonePoints": {"Z1": 225, "Z2": 213, "Z3": 230, "Z4": 224, "Z5": 243, "Z6": 243, "Z7": 261, "Z8": 266, "Z9": 279, "Z10": 309, "Z11": 323, "Z12": 378}, "page": 28},
    {"reference": "40A2V1200", "name": "Alto 2 Vitrinas 1200mm", "category": "ALTOS", "series": "PROGRAMA ESTANDAR", "module": "ALTO 2 VITRINAS", "height": 400, "depth": 330, "width": 1200, "code": "40A2V1200", "points": 247, "zonePoints": {"Z1": 247, "Z2": 230, "Z3": 247, "Z4": 243, "Z5": 264, "Z6": 267, "Z7": 286, "Z8": 291, "Z9": 306, "Z10": 314, "Z11": 331, "Z12": 391}, "page": 28},
    
    # ========== PÁGINA 89-94: SOBREMÓDULOS ==========
    # Sobremódulo 1 puerta (página 89)
    {"reference": "11SM1P400", "name": "Sobremódulo 1 puerta 400mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 PUERTA", "height": 1100, "depth": 330, "width": 400, "code": "11SM1P400", "points": 137, "zonePoints": {"Z1": 137, "Z2": 141, "Z3": 152, "Z4": 151, "Z5": 164, "Z6": 183, "Z7": 197, "Z8": 201, "Z9": 211, "Z10": 214, "Z11": 226, "Z12": 261}, "page": 89},
    {"reference": "11SM1P450", "name": "Sobremódulo 1 puerta 450mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 PUERTA", "height": 1100, "depth": 330, "width": 450, "code": "11SM1P450", "points": 143, "zonePoints": {"Z1": 143, "Z2": 148, "Z3": 161, "Z4": 161, "Z5": 176, "Z6": 193, "Z7": 208, "Z8": 213, "Z9": 224, "Z10": 223, "Z11": 230, "Z12": 270}, "page": 89},
    {"reference": "11SM1P500", "name": "Sobremódulo 1 puerta 500mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 PUERTA", "height": 1100, "depth": 330, "width": 500, "code": "11SM1P500", "points": 151, "zonePoints": {"Z1": 151, "Z2": 155, "Z3": 170, "Z4": 171, "Z5": 187, "Z6": 204, "Z7": 221, "Z8": 225, "Z9": 237, "Z10": 232, "Z11": 239, "Z12": 278}, "page": 89},
    {"reference": "11SM1P600", "name": "Sobremódulo 1 puerta 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 PUERTA", "height": 1100, "depth": 330, "width": 600, "code": "11SM1P600", "points": 164, "zonePoints": {"Z1": 164, "Z2": 170, "Z3": 185, "Z4": 190, "Z5": 211, "Z6": 217, "Z7": 235, "Z8": 239, "Z9": 252, "Z10": 249, "Z11": 256, "Z12": 295}, "page": 89},
    {"reference": "11SM1P650", "name": "Sobremódulo 1 puerta 650mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 PUERTA", "height": 1100, "depth": 330, "width": 650, "code": "11SM1P650", "points": 184, "zonePoints": {"Z1": 184, "Z2": 190, "Z3": 205, "Z4": 209, "Z5": 230, "Z6": 237, "Z7": 255, "Z8": 259, "Z9": 272, "Z10": 269, "Z11": 276, "Z12": 315}, "page": 89},
    
    # Sobremódulo 2 puertas (página 89)
    {"reference": "11SM2P600", "name": "Sobremódulo 2 puertas 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 600, "code": "11SM2P600", "points": 205, "zonePoints": {"Z1": 205, "Z2": 213, "Z3": 230, "Z4": 221, "Z5": 240, "Z6": 294, "Z7": 318, "Z8": 323, "Z9": 342, "Z10": 345, "Z11": 360, "Z12": 437}, "page": 89},
    {"reference": "11SM2P700", "name": "Sobremódulo 2 puertas 700mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 700, "code": "11SM2P700", "points": 217, "zonePoints": {"Z1": 217, "Z2": 226, "Z3": 246, "Z4": 239, "Z5": 263, "Z6": 311, "Z7": 337, "Z8": 343, "Z9": 363, "Z10": 361, "Z11": 386, "Z12": 453}, "page": 89},
    {"reference": "11SM2P800", "name": "Sobremódulo 2 puertas 800mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 800, "code": "11SM2P800", "points": 231, "zonePoints": {"Z1": 231, "Z2": 239, "Z3": 261, "Z4": 258, "Z5": 285, "Z6": 319, "Z7": 345, "Z8": 352, "Z9": 373, "Z10": 378, "Z11": 400, "Z12": 468}, "page": 89},
    {"reference": "11SM2P900", "name": "Sobremódulo 2 puertas 900mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 900, "code": "11SM2P900", "points": 244, "zonePoints": {"Z1": 244, "Z2": 253, "Z3": 276, "Z4": 276, "Z5": 306, "Z6": 339, "Z7": 368, "Z8": 375, "Z9": 397, "Z10": 395, "Z11": 410, "Z12": 484}, "page": 89},
    {"reference": "11SM2P1000", "name": "Sobremódulo 2 puertas 1000mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 1000, "code": "11SM2P1000", "points": 257, "zonePoints": {"Z1": 257, "Z2": 268, "Z3": 293, "Z4": 295, "Z5": 328, "Z6": 360, "Z7": 391, "Z8": 398, "Z9": 422, "Z10": 412, "Z11": 426, "Z12": 501}, "page": 89},
    {"reference": "11SM2P1200", "name": "Sobremódulo 2 puertas 1200mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 1200, "code": "11SM2P1200", "points": 284, "zonePoints": {"Z1": 284, "Z2": 294, "Z3": 323, "Z4": 333, "Z5": 372, "Z6": 384, "Z7": 417, "Z8": 425, "Z9": 452, "Z10": 445, "Z11": 459, "Z12": 532}, "page": 89},
    {"reference": "11SM2P1300", "name": "Sobremódulo 2 puertas 1300mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS", "height": 1100, "depth": 330, "width": 1300, "code": "11SM2P1300", "points": 310, "zonePoints": {"Z1": 310, "Z2": 320, "Z3": 350, "Z4": 359, "Z5": 398, "Z6": 411, "Z7": 443, "Z8": 452, "Z9": 478, "Z10": 471, "Z11": 485, "Z12": 559}, "page": 89},
    
    # Sobremódulo 2 puertas plegables (página 89)
    {"reference": "11SM2PPL700", "name": "Sobremódulo 2 puertas plegables 700mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 700, "code": "11SM2PPL700", "points": 374, "zonePoints": {"Z1": 374, "Z2": 382, "Z3": 402, "Z4": 396, "Z5": 419, "Z6": 467, "Z7": 494, "Z8": 500, "Z9": 520, "Z10": 518, "Z11": 543, "Z12": 609}, "page": 89},
    {"reference": "11SM2PPL800", "name": "Sobremódulo 2 puertas plegables 800mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 800, "code": "11SM2PPL800", "points": 387, "zonePoints": {"Z1": 387, "Z2": 396, "Z3": 418, "Z4": 415, "Z5": 441, "Z6": 476, "Z7": 502, "Z8": 508, "Z9": 529, "Z10": 534, "Z11": 557, "Z12": 625}, "page": 89},
    {"reference": "11SM2PPL900", "name": "Sobremódulo 2 puertas plegables 900mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 900, "code": "11SM2PPL900", "points": 400, "zonePoints": {"Z1": 400, "Z2": 410, "Z3": 433, "Z4": 433, "Z5": 462, "Z6": 496, "Z7": 524, "Z8": 531, "Z9": 553, "Z10": 551, "Z11": 566, "Z12": 641}, "page": 89},
    {"reference": "11SM2PPL1000", "name": "Sobremódulo 2 puertas plegables 1000mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 1000, "code": "11SM2PPL1000", "points": 414, "zonePoints": {"Z1": 414, "Z2": 424, "Z3": 449, "Z4": 452, "Z5": 484, "Z6": 517, "Z7": 547, "Z8": 554, "Z9": 579, "Z10": 568, "Z11": 583, "Z12": 657}, "page": 89},
    {"reference": "11SM2PPL1200", "name": "Sobremódulo 2 puertas plegables 1200mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 1200, "code": "11SM2PPL1200", "points": 440, "zonePoints": {"Z1": 440, "Z2": 450, "Z3": 480, "Z4": 489, "Z5": 528, "Z6": 541, "Z7": 573, "Z8": 582, "Z9": 608, "Z10": 602, "Z11": 615, "Z12": 689}, "page": 89},
    {"reference": "11SM2PPL1300", "name": "Sobremódulo 2 puertas plegables 1300mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 PUERTAS PLEGABLES", "height": 1100, "depth": 330, "width": 1300, "code": "11SM2PPL1300", "points": 466, "zonePoints": {"Z1": 466, "Z2": 477, "Z3": 506, "Z4": 516, "Z5": 554, "Z6": 567, "Z7": 600, "Z8": 608, "Z9": 634, "Z10": 628, "Z11": 642, "Z12": 715}, "page": 89},
    
    # Sobremódulo 1 Vitrina (página 89)
    {"reference": "11SM1V400", "name": "Sobremódulo 1 Vitrina 400mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 VITRINA", "height": 1100, "depth": 330, "width": 400, "code": "11SM1V400", "points": 205, "zonePoints": {"Z1": 205, "Z2": 209, "Z3": 220, "Z4": 219, "Z5": 233, "Z6": 251, "Z7": 266, "Z8": 269, "Z9": 279, "Z10": 282, "Z11": 294, "Z12": 330}, "page": 89},
    {"reference": "11SM1V450", "name": "Sobremódulo 1 Vitrina 450mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 VITRINA", "height": 1100, "depth": 330, "width": 450, "code": "11SM1V450", "points": 212, "zonePoints": {"Z1": 212, "Z2": 216, "Z3": 229, "Z4": 229, "Z5": 245, "Z6": 261, "Z7": 272, "Z8": 289, "Z9": 291, "Z10": 299, "Z11": 300, "Z12": 346}, "page": 89},
    {"reference": "11SM1V500", "name": "Sobremódulo 1 Vitrina 500mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 VITRINA", "height": 1100, "depth": 330, "width": 500, "code": "11SM1V500", "points": 219, "zonePoints": {"Z1": 219, "Z2": 224, "Z3": 238, "Z4": 239, "Z5": 256, "Z6": 272, "Z7": 289, "Z8": 293, "Z9": 305, "Z10": 300, "Z11": 307, "Z12": 346}, "page": 89},
    {"reference": "11SM1V600", "name": "Sobremódulo 1 Vitrina 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 VITRINA", "height": 1100, "depth": 330, "width": 600, "code": "11SM1V600", "points": 233, "zonePoints": {"Z1": 233, "Z2": 238, "Z3": 253, "Z4": 258, "Z5": 279, "Z6": 285, "Z7": 303, "Z8": 307, "Z9": 321, "Z10": 317, "Z11": 324, "Z12": 364}, "page": 89},
    {"reference": "11SM1V650", "name": "Sobremódulo 1 Vitrina 650mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 1 VITRINA", "height": 1100, "depth": 330, "width": 650, "code": "11SM1V650", "points": 252, "zonePoints": {"Z1": 252, "Z2": 258, "Z3": 273, "Z4": 278, "Z5": 299, "Z6": 305, "Z7": 323, "Z8": 327, "Z9": 341, "Z10": 337, "Z11": 344, "Z12": 384}, "page": 89},
    
    # Sobremódulo 2 vitrinas (página 90)
    {"reference": "11SM2V600", "name": "Sobremódulo 2 vitrinas 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 600, "code": "11SM2V600", "points": 350, "zonePoints": {"Z1": 350, "Z2": 358, "Z3": 375, "Z4": 365, "Z5": 385, "Z6": 439, "Z7": 463, "Z8": 468, "Z9": 487, "Z10": 490, "Z11": 505, "Z12": 582}, "page": 90},
    {"reference": "11SM2V700", "name": "Sobremódulo 2 vitrinas 700mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 700, "code": "11SM2V700", "points": 362, "zonePoints": {"Z1": 362, "Z2": 371, "Z3": 391, "Z4": 384, "Z5": 407, "Z6": 456, "Z7": 482, "Z8": 488, "Z9": 508, "Z10": 506, "Z11": 531, "Z12": 597}, "page": 90},
    {"reference": "11SM2V800", "name": "Sobremódulo 2 vitrinas 800mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 800, "code": "11SM2V800", "points": 376, "zonePoints": {"Z1": 376, "Z2": 384, "Z3": 406, "Z4": 403, "Z5": 429, "Z6": 464, "Z7": 490, "Z8": 497, "Z9": 518, "Z10": 523, "Z11": 545, "Z12": 613}, "page": 90},
    {"reference": "11SM2V900", "name": "Sobremódulo 2 vitrinas 900mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 900, "code": "11SM2V900", "points": 389, "zonePoints": {"Z1": 389, "Z2": 398, "Z3": 421, "Z4": 421, "Z5": 450, "Z6": 484, "Z7": 512, "Z8": 520, "Z9": 542, "Z10": 540, "Z11": 554, "Z12": 629}, "page": 90},
    {"reference": "11SM2V1000", "name": "Sobremódulo 2 vitrinas 1000mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 1000, "code": "11SM2V1000", "points": 402, "zonePoints": {"Z1": 402, "Z2": 413, "Z3": 438, "Z4": 440, "Z5": 473, "Z6": 505, "Z7": 536, "Z8": 543, "Z9": 567, "Z10": 557, "Z11": 571, "Z12": 646}, "page": 90},
    {"reference": "11SM2V1200", "name": "Sobremódulo 2 vitrinas 1200mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 1200, "code": "11SM2V1200", "points": 428, "zonePoints": {"Z1": 428, "Z2": 439, "Z3": 468, "Z4": 478, "Z5": 517, "Z6": 529, "Z7": 562, "Z8": 570, "Z9": 596, "Z10": 590, "Z11": 604, "Z12": 677}, "page": 90},
    {"reference": "11SM2V1300", "name": "Sobremódulo 2 vitrinas 1300mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO 2 VITRINAS", "height": 1100, "depth": 330, "width": 1300, "code": "11SM2V1300", "points": 455, "zonePoints": {"Z1": 455, "Z2": 465, "Z3": 495, "Z4": 504, "Z5": 543, "Z6": 555, "Z7": 588, "Z8": 596, "Z9": 623, "Z10": 616, "Z11": 630, "Z12": 704}, "page": 90},
    
    # Sobremódulo horno (página 94)
    {"reference": "11SMH1P600", "name": "Sobremódulo horno 1 Puerta 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO HORNO 1 PUERTA", "height": 1100, "depth": 580, "width": 600, "code": "11SMH1P600", "points": 165, "zonePoints": {"Z1": 165, "Z2": 173, "Z3": 185, "Z4": 181, "Z5": 196, "Z6": 198, "Z7": 209, "Z8": 213, "Z9": 221, "Z10": 246, "Z11": 255, "Z12": 289}, "page": 94},
    {"reference": "11SMH2P600", "name": "Sobremódulo horno 2 Puertas 600mm", "category": "SOBREMÓDULOS", "series": "PROGRAMA ESTANDAR", "module": "SOBREMÓDULO HORNO 2 PUERTAS", "height": 1100, "depth": 580, "width": 600, "code": "11SMH2P600", "points": 175, "zonePoints": {"Z1": 175, "Z2": 182, "Z3": 192, "Z4": 189, "Z5": 202, "Z6": 204, "Z7": 213, "Z8": 216, "Z9": 224, "Z10": 246, "Z11": 253, "Z12": 282}, "page": 94},
]

async def import_products():
    """Import products to the database, updating existing ones"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    products_collection = db.products
    
    count_before = await products_collection.count_documents({})
    print(f"📊 Productos antes de importar: {count_before}")
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for product in PRODUCTS_PAGES_28_94:
        existing = await products_collection.find_one({"reference": product["reference"]})
        
        if existing:
            result = await products_collection.update_one(
                {"reference": product["reference"]},
                {"$set": {**product, "updatedAt": datetime.utcnow()}}
            )
            if result.modified_count > 0:
                updated += 1
            else:
                skipped += 1
        else:
            product["createdAt"] = datetime.utcnow()
            product["updatedAt"] = datetime.utcnow()
            await products_collection.insert_one(product)
            inserted += 1
    
    count_after = await products_collection.count_documents({})
    
    print("\n" + "="*60)
    print(f"📋 RESUMEN DE IMPORTACIÓN - Páginas 28-94 (Muestra)")
    print("="*60)
    print(f"✅ Nuevos productos insertados: {inserted}")
    print(f"🔄 Productos actualizados: {updated}")
    print(f"⏭️  Productos sin cambios: {skipped}")
    print(f"📊 Total productos en BD: {count_after}")
    print("="*60)
    
    client.close()
    return inserted, updated, count_after

if __name__ == "__main__":
    asyncio.run(import_products())
