#!/usr/bin/env python3
"""
Process pages 55-59 from TARIFA-TECNICA-ZONACOCINAS
Extract all product references and add to database
"""
import json
import os
from pymongo import MongoClient
import uuid

# Connect to MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Products extracted from pages 55-59
products_data = [
    # PAGE 55 - ALTOS 70 FONDO 58
    # Alto 2 puertas plegables HF fondo 580mm
    {"reference": "7A2PPL58600", "name": "Alto 2 puertas plegables HF fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 281, "Z2": 288, "Z3": 301, "Z4": 312, "Z5": 332, "Z6": 323, "Z7": 338, "Z8": 341, "Z9": 353, "Z10": 401, "Z11": 417, "Z12": 477}},
    {"reference": "7A2PPL58700", "name": "Alto 2 puertas plegables HF fondo 580mm 70cm", "series": "ALTOS 70 FONDO 58", "ancho": 70, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 294, "Z2": 300, "Z3": 316, "Z4": 323, "Z5": 344, "Z6": 340, "Z7": 356, "Z8": 360, "Z9": 373, "Z10": 494, "Z11": 523, "Z12": 603}},
    {"reference": "7A2PPL58800", "name": "Alto 2 puertas plegables HF fondo 580mm 80cm", "series": "ALTOS 70 FONDO 58", "ancho": 80, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 319, "Z2": 328, "Z3": 344, "Z4": 356, "Z5": 381, "Z6": 389, "Z7": 410, "Z8": 415, "Z9": 432, "Z10": 512, "Z11": 542, "Z12": 622}},
    {"reference": "7A2PPL58900", "name": "Alto 2 puertas plegables HF fondo 580mm 90cm", "series": "ALTOS 70 FONDO 58", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 331, "Z2": 339, "Z3": 358, "Z4": 371, "Z5": 399, "Z6": 423, "Z7": 449, "Z8": 456, "Z9": 476, "Z10": 518, "Z11": 546, "Z12": 626}},
    {"reference": "7A2PPL581000", "name": "Alto 2 puertas plegables HF fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 362, "Z2": 375, "Z3": 401, "Z4": 399, "Z5": 433, "Z6": 492, "Z7": 529, "Z8": 538, "Z9": 566, "Z10": 567, "Z11": 581, "Z12": 670}},
    {"reference": "7A2PPL581200", "name": "Alto 2 puertas plegables HF fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 373, "Z2": 384, "Z3": 412, "Z4": 408, "Z5": 442, "Z6": 503, "Z7": 539, "Z8": 547, "Z9": 575, "Z10": 578, "Z11": 590, "Z12": 680}},
    
    # Alto 2 vitrinas plegables HF fondo 580mm
    {"reference": "7A2VPL58600", "name": "Alto 2 vitrinas plegables HF fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 365, "Z2": 338, "Z3": 352, "Z4": 363, "Z5": 383, "Z6": 358, "Z7": 373, "Z8": 376, "Z9": 387, "Z10": 436, "Z11": 452, "Z12": 512}},
    {"reference": "7A2VPL58700", "name": "Alto 2 vitrinas plegables HF fondo 580mm 70cm", "series": "ALTOS 70 FONDO 58", "ancho": 70, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 384, "Z2": 357, "Z3": 373, "Z4": 381, "Z5": 402, "Z6": 381, "Z7": 397, "Z8": 401, "Z9": 414, "Z10": 534, "Z11": 564, "Z12": 644}},
    {"reference": "7A2VPL58800", "name": "Alto 2 vitrinas plegables HF fondo 580mm 80cm", "series": "ALTOS 70 FONDO 58", "ancho": 80, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 417, "Z2": 390, "Z3": 407, "Z4": 420, "Z5": 445, "Z6": 436, "Z7": 457, "Z8": 462, "Z9": 479, "Z10": 560, "Z11": 589, "Z12": 668}},
    {"reference": "7A2VPL58900", "name": "Alto 2 vitrinas plegables HF fondo 580mm 90cm", "series": "ALTOS 70 FONDO 58", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 436, "Z2": 408, "Z3": 427, "Z4": 441, "Z5": 468, "Z6": 477, "Z7": 503, "Z8": 509, "Z9": 529, "Z10": 570, "Z11": 600, "Z12": 679}},
    {"reference": "7A2VPL581000", "name": "Alto 2 vitrinas plegables HF fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 455, "Z2": 449, "Z3": 477, "Z4": 476, "Z5": 508, "Z6": 552, "Z7": 588, "Z8": 596, "Z9": 625, "Z10": 627, "Z11": 639, "Z12": 730}},
    {"reference": "7A2VPL581200", "name": "Alto 2 vitrinas plegables HF fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 492, "Z2": 473, "Z3": 499, "Z4": 498, "Z5": 531, "Z6": 574, "Z7": 610, "Z8": 620, "Z9": 647, "Z10": 649, "Z11": 663, "Z12": 752}},
    
    # Alto 1 vitrina 1 puerta plegable HF fondo 580mm
    {"reference": "7A1V1PPL58600", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 322, "Z2": 312, "Z3": 326, "Z4": 337, "Z5": 357, "Z6": 339, "Z7": 354, "Z8": 357, "Z9": 369, "Z10": 417, "Z11": 433, "Z12": 494}},
    {"reference": "7A1V1PPL58700", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 70cm", "series": "ALTOS 70 FONDO 58", "ancho": 70, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 338, "Z2": 328, "Z3": 343, "Z4": 351, "Z5": 373, "Z6": 359, "Z7": 376, "Z8": 380, "Z9": 393, "Z10": 513, "Z11": 543, "Z12": 622}},
    {"reference": "7A1V1PPL58800", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 80cm", "series": "ALTOS 70 FONDO 58", "ancho": 80, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 366, "Z2": 357, "Z3": 375, "Z4": 386, "Z5": 412, "Z6": 411, "Z7": 433, "Z8": 437, "Z9": 454, "Z10": 534, "Z11": 564, "Z12": 644}},
    {"reference": "7A1V1PPL58900", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 90cm", "series": "ALTOS 70 FONDO 58", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 382, "Z2": 373, "Z3": 392, "Z4": 405, "Z5": 433, "Z6": 449, "Z7": 475, "Z8": 481, "Z9": 502, "Z10": 543, "Z11": 572, "Z12": 652}},
    {"reference": "7A1V1PPL581000", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 407, "Z2": 412, "Z3": 438, "Z4": 436, "Z5": 469, "Z6": 522, "Z7": 558, "Z8": 566, "Z9": 594, "Z10": 595, "Z11": 609, "Z12": 698}},
    {"reference": "7A1V1PPL581200", "name": "Alto 1 vitrina 1 puerta plegable HF fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 432, "Z2": 427, "Z3": 454, "Z4": 453, "Z5": 485, "Z6": 538, "Z7": 573, "Z8": 582, "Z9": 610, "Z10": 612, "Z11": 625, "Z12": 715}},
    
    # Alto microondas 1 puerta fondo 580mm (Derecha/Izquierda)
    {"reference": "7AM1P58600", "name": "Alto microondas 1 puerta fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 55,
     "zonePoints": {"Z1": 151, "Z2": 153, "Z3": 161, "Z4": 166, "Z5": 176, "Z6": 171, "Z7": 179, "Z8": 181, "Z9": 186, "Z10": 210, "Z11": 218, "Z12": 249}},
    
    # PAGE 56 - ALTOS 70 FONDO 58
    # Alto microondas 1 puerta abatible HK fondo 580mm
    {"reference": "7AM1PABL58600", "name": "Alto microondas 1 puerta abatible HK fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 56,
     "zonePoints": {"Z1": 213, "Z2": 215, "Z3": 223, "Z4": 228, "Z5": 238, "Z6": 233, "Z7": 240, "Z8": 243, "Z9": 248, "Z10": 272, "Z11": 280, "Z12": 311}},
    
    # Alto microondas 2 puertas
    {"reference": "7AM2P58600", "name": "Alto microondas 2 puertas 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 56,
     "zonePoints": {"Z1": 195, "Z2": 197, "Z3": 206, "Z4": 212, "Z5": 225, "Z6": 247, "Z7": 259, "Z8": 263, "Z9": 272, "Z10": 310, "Z11": 322, "Z12": 374}},
    
    # Alto microondas 1 vitrina (Derecha/Izquierda)
    {"reference": "7AM1V58600", "name": "Alto microondas 1 vitrina 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 56,
     "zonePoints": {"Z1": 189, "Z2": 177, "Z3": 184, "Z4": 190, "Z5": 201, "Z6": 187, "Z7": 194, "Z8": 196, "Z9": 202, "Z10": 226, "Z11": 234, "Z12": 265}},
    
    # Alto microondas 1 vitrina abatible fondo 580mm
    {"reference": "7AM1VABL58600", "name": "Alto microondas 1 vitrina abatible fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 56,
     "zonePoints": {"Z1": 247, "Z2": 235, "Z3": 242, "Z4": 248, "Z5": 258, "Z6": 245, "Z7": 252, "Z8": 254, "Z9": 259, "Z10": 284, "Z11": 292, "Z12": 322}},
    
    # PAGE 57 - ALTOS 70 FONDO 58
    # Alto microondas 2 vitrinas fondo 580mm
    {"reference": "7AM12V58600", "name": "Alto microondas 2 vitrinas fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 257, "Z2": 230, "Z3": 237, "Z4": 245, "Z5": 257, "Z6": 263, "Z7": 275, "Z8": 278, "Z9": 289, "Z10": 326, "Z11": 339, "Z12": 391}},
    
    # Alto rincón angular 2 puertas fondo 580mm
    {"reference": "7ARA2P58630", "name": "Alto rincón angular 2 puertas fondo 580mm 63cm", "series": "ALTOS 70 FONDO 58", "ancho": 63, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 231, "Z2": 237, "Z3": 252, "Z4": 242, "Z5": 256, "Z6": 280, "Z7": 296, "Z8": 300, "Z9": 313, "Z10": 341, "Z11": 357, "Z12": 418}},
    {"reference": "7ARA2P58730", "name": "Alto rincón angular 2 puertas fondo 580mm 73cm", "series": "ALTOS 70 FONDO 58", "ancho": 73, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 257, "Z2": 264, "Z3": 278, "Z4": 268, "Z5": 282, "Z6": 307, "Z7": 322, "Z8": 327, "Z9": 339, "Z10": 368, "Z11": 383, "Z12": 444}},
    {"reference": "7ARA2P58830", "name": "Alto rincón angular 2 puertas fondo 580mm 83cm", "series": "ALTOS 70 FONDO 58", "ancho": 83, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 284, "Z2": 290, "Z3": 305, "Z4": 294, "Z5": 309, "Z6": 333, "Z7": 349, "Z8": 353, "Z9": 365, "Z10": 394, "Z11": 410, "Z12": 470}},
    {"reference": "7ARA2P58930", "name": "Alto rincón angular 2 puertas fondo 580mm 93cm", "series": "ALTOS 70 FONDO 58", "ancho": 93, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 299, "Z2": 306, "Z3": 320, "Z4": 310, "Z5": 324, "Z6": 349, "Z7": 364, "Z8": 369, "Z9": 381, "Z10": 410, "Z11": 425, "Z12": 486}},
    {"reference": "7ARA2P581030", "name": "Alto rincón angular 2 puertas fondo 580mm 103cm", "series": "ALTOS 70 FONDO 58", "ancho": 103, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 313, "Z2": 319, "Z3": 334, "Z4": 323, "Z5": 338, "Z6": 362, "Z7": 378, "Z8": 382, "Z9": 395, "Z10": 423, "Z11": 439, "Z12": 500}},
    
    # Alto rincón angular 1 puerta fondo 580mm (Derecha/Izquierda)
    {"reference": "7ARA1P58630", "name": "Alto rincón angular 1 puerta fondo 580mm 63cm", "series": "ALTOS 70 FONDO 58", "ancho": 63, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 231, "Z2": 237, "Z3": 252, "Z4": 242, "Z5": 256, "Z6": 280, "Z7": 296, "Z8": 300, "Z9": 313, "Z10": 341, "Z11": 357, "Z12": 418}},
    {"reference": "7ARA1P58730", "name": "Alto rincón angular 1 puerta fondo 580mm 73cm", "series": "ALTOS 70 FONDO 58", "ancho": 73, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 257, "Z2": 264, "Z3": 278, "Z4": 268, "Z5": 282, "Z6": 307, "Z7": 322, "Z8": 327, "Z9": 339, "Z10": 273, "Z11": 383, "Z12": 444}},
    {"reference": "7ARA1P58830", "name": "Alto rincón angular 1 puerta fondo 580mm 83cm", "series": "ALTOS 70 FONDO 58", "ancho": 83, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 284, "Z2": 290, "Z3": 305, "Z4": 294, "Z5": 309, "Z6": 333, "Z7": 349, "Z8": 353, "Z9": 365, "Z10": 394, "Z11": 410, "Z12": 470}},
    {"reference": "7ARA1P58930", "name": "Alto rincón angular 1 puerta fondo 580mm 93cm", "series": "ALTOS 70 FONDO 58", "ancho": 93, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 299, "Z2": 306, "Z3": 320, "Z4": 310, "Z5": 324, "Z6": 349, "Z7": 364, "Z8": 369, "Z9": 381, "Z10": 410, "Z11": 425, "Z12": 486}},
    
    # Alto rincón lineal 1 puerta fondo 580mm (Derecha/Izquierda)
    {"reference": "7ARC1P58900", "name": "Alto rincón lineal 1 puerta fondo 580mm 90cm", "series": "ALTOS 70 FONDO 58", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 165, "Z2": 170, "Z3": 176, "Z4": 169, "Z5": 180, "Z6": 191, "Z7": 201, "Z8": 201, "Z9": 208, "Z10": 237, "Z11": 246, "Z12": 276}},
    {"reference": "7ARC1P58950", "name": "Alto rincón lineal 1 puerta fondo 580mm 95cm", "series": "ALTOS 70 FONDO 58", "ancho": 95, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 168, "Z2": 172, "Z3": 180, "Z4": 172, "Z5": 182, "Z6": 194, "Z7": 204, "Z8": 204, "Z9": 211, "Z10": 240, "Z11": 249, "Z12": 279}},
    {"reference": "7ARC1P581000", "name": "Alto rincón lineal 1 puerta fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 174, "Z2": 179, "Z3": 187, "Z4": 179, "Z5": 190, "Z6": 198, "Z7": 209, "Z8": 209, "Z9": 216, "Z10": 248, "Z11": 256, "Z12": 286}},
    {"reference": "7ARC1P581050", "name": "Alto rincón lineal 1 puerta fondo 580mm 105cm", "series": "ALTOS 70 FONDO 58", "ancho": 105, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 181, "Z2": 185, "Z3": 193, "Z4": 186, "Z5": 198, "Z6": 204, "Z7": 215, "Z8": 215, "Z9": 223, "Z10": 255, "Z11": 264, "Z12": 293}},
    {"reference": "7ARC1P581100", "name": "Alto rincón lineal 1 puerta fondo 580mm 110cm", "series": "ALTOS 70 FONDO 58", "ancho": 110, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 185, "Z2": 190, "Z3": 200, "Z4": 193, "Z5": 207, "Z6": 211, "Z7": 223, "Z8": 223, "Z9": 231, "Z10": 260, "Z11": 269, "Z12": 298}},
    {"reference": "7ARC1P581150", "name": "Alto rincón lineal 1 puerta fondo 580mm 115cm", "series": "ALTOS 70 FONDO 58", "ancho": 115, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 191, "Z2": 196, "Z3": 207, "Z4": 202, "Z5": 216, "Z6": 219, "Z7": 232, "Z8": 232, "Z9": 242, "Z10": 269, "Z11": 277, "Z12": 307}},
    {"reference": "7ARC1P581200", "name": "Alto rincón lineal 1 puerta fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 57,
     "zonePoints": {"Z1": 201, "Z2": 207, "Z3": 218, "Z4": 215, "Z5": 232, "Z6": 235, "Z7": 249, "Z8": 250, "Z9": 260, "Z10": 281, "Z11": 289, "Z12": 318}},
    
    # PAGE 58 - ALTOS 70 FONDO 58
    # Alto rincón lineal 2 puertas fondo 580mm
    {"reference": "7ARC2P581000", "name": "Alto rincón lineal 2 puertas fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 184, "Z2": 195, "Z3": 212, "Z4": 205, "Z5": 231, "Z6": 234, "Z7": 255, "Z8": 255, "Z9": 273, "Z10": 300, "Z11": 314, "Z12": 356}},
    {"reference": "7ARC2P581100", "name": "Alto rincón lineal 2 puertas fondo 580mm 110cm", "series": "ALTOS 70 FONDO 58", "ancho": 110, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 208, "Z2": 219, "Z3": 235, "Z4": 229, "Z5": 254, "Z6": 257, "Z7": 278, "Z8": 278, "Z9": 296, "Z10": 324, "Z11": 337, "Z12": 379}},
    {"reference": "7ARC2P581200", "name": "Alto rincón lineal 2 puertas fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 236, "Z2": 245, "Z3": 261, "Z4": 257, "Z5": 284, "Z6": 286, "Z7": 308, "Z8": 308, "Z9": 326, "Z10": 352, "Z11": 366, "Z12": 408}},
    {"reference": "7ARC2P581300", "name": "Alto rincón lineal 2 puertas fondo 580mm 130cm", "series": "ALTOS 70 FONDO 58", "ancho": 130, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 257, "Z2": 266, "Z3": 282, "Z4": 278, "Z5": 305, "Z6": 307, "Z7": 329, "Z8": 317, "Z9": 347, "Z10": 373, "Z11": 387, "Z12": 428}},
    
    # Alto termo 1 puerta fondo 580mm (Derecha/Izquierda)
    {"reference": "7AT1P58400", "name": "Alto termo 1 puerta fondo 580mm 40cm", "series": "ALTOS 70 FONDO 58", "ancho": 40, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 86, "Z2": 89, "Z3": 100, "Z4": 96, "Z5": 106, "Z6": 111, "Z7": 121, "Z8": 124, "Z9": 131, "Z10": 150, "Z11": 160, "Z12": 193}},
    {"reference": "7AT1P58450", "name": "Alto termo 1 puerta fondo 580mm 45cm", "series": "ALTOS 70 FONDO 58", "ancho": 45, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 90, "Z2": 96, "Z3": 106, "Z4": 101, "Z5": 114, "Z6": 119, "Z7": 129, "Z8": 131, "Z9": 140, "Z10": 156, "Z11": 165, "Z12": 198}},
    {"reference": "7AT1P58500", "name": "Alto termo 1 puerta fondo 580mm 50cm", "series": "ALTOS 70 FONDO 58", "ancho": 50, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 96, "Z2": 100, "Z3": 110, "Z4": 107, "Z5": 121, "Z6": 125, "Z7": 137, "Z8": 139, "Z9": 148, "Z10": 163, "Z11": 170, "Z12": 205}},
    {"reference": "7AT1P58600", "name": "Alto termo 1 puerta fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 104, "Z2": 108, "Z3": 121, "Z4": 120, "Z5": 137, "Z6": 139, "Z7": 153, "Z8": 156, "Z9": 167, "Z10": 173, "Z11": 181, "Z12": 215}},
    
    # Alto termo 2 puertas fondo 580mm
    {"reference": "7AT2P58600", "name": "Alto termo 2 puertas fondo 580mm 60cm", "series": "ALTOS 70 FONDO 58", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 130, "Z2": 141, "Z3": 155, "Z4": 146, "Z5": 160, "Z6": 160, "Z7": 183, "Z8": 315, "Z9": 202, "Z10": 239, "Z11": 255, "Z12": 314}},
    {"reference": "7AT2P58700", "name": "Alto termo 2 puertas fondo 580mm 70cm", "series": "ALTOS 70 FONDO 58", "ancho": 70, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 147, "Z2": 154, "Z3": 168, "Z4": 159, "Z5": 175, "Z6": 192, "Z7": 207, "Z8": 210, "Z9": 223, "Z10": 267, "Z11": 278, "Z12": 327}},
    {"reference": "7AT2P58800", "name": "Alto termo 2 puertas fondo 580mm 80cm", "series": "ALTOS 70 FONDO 58", "ancho": 80, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 158, "Z2": 164, "Z3": 180, "Z4": 173, "Z5": 190, "Z6": 200, "Z7": 217, "Z8": 222, "Z9": 234, "Z10": 267, "Z11": 281, "Z12": 340}},
    {"reference": "7AT2P58900", "name": "Alto termo 2 puertas fondo 580mm 90cm", "series": "ALTOS 70 FONDO 58", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 167, "Z2": 174, "Z3": 193, "Z4": 187, "Z5": 207, "Z6": 215, "Z7": 234, "Z8": 237, "Z9": 252, "Z10": 280, "Z11": 294, "Z12": 352}},
    {"reference": "7AT2P581000", "name": "Alto termo 2 puertas fondo 580mm 100cm", "series": "ALTOS 70 FONDO 58", "ancho": 100, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 179, "Z2": 187, "Z3": 207, "Z4": 200, "Z5": 224, "Z6": 229, "Z7": 249, "Z8": 254, "Z9": 269, "Z10": 293, "Z11": 307, "Z12": 364}},
    {"reference": "7AT2P581200", "name": "Alto termo 2 puertas fondo 580mm 120cm", "series": "ALTOS 70 FONDO 58", "ancho": 120, "alto": 70, "fondo": 58, "sourcePage": 58,
     "zonePoints": {"Z1": 200, "Z2": 208, "Z3": 231, "Z4": 228, "Z5": 256, "Z6": 261, "Z7": 285, "Z8": 290, "Z9": 307, "Z10": 320, "Z11": 334, "Z12": 390}},
    
    # PAGE 59 - ALTOS 70cm DECORATIVOS
    # Alto Decorativo fondo 33cm (1 estante)
    {"reference": "7ADEC150", "name": "Alto Decorativo fondo 33cm 15cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 15, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 152, "Z2": 175, "Z3": 148, "Z4": 134, "Z5": 154, "Z6": 184, "Z7": 197, "Z8": 184, "Z9": 197, "Z10": 191, "Z11": 191, "Z12": 191}},
    {"reference": "7ADEC200", "name": "Alto Decorativo fondo 33cm 20cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 20, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 166, "Z2": 188, "Z3": 161, "Z4": 146, "Z5": 169, "Z6": 194, "Z7": 208, "Z8": 194, "Z9": 208, "Z10": 201, "Z11": 201, "Z12": 201}},
    {"reference": "7ADEC300", "name": "Alto Decorativo fondo 33cm 30cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 30, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 172, "Z2": 195, "Z3": 165, "Z4": 148, "Z5": 173, "Z6": 205, "Z7": 212, "Z8": 205, "Z9": 221, "Z10": 212, "Z11": 212, "Z12": 212}},
    {"reference": "7ADEC350", "name": "Alto Decorativo fondo 33cm 35cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 35, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 197, "Z2": 227, "Z3": 194, "Z4": 174, "Z5": 203, "Z6": 239, "Z7": 250, "Z8": 239, "Z9": 257, "Z10": 250, "Z11": 250, "Z12": 250}},
    {"reference": "7ADEC400", "name": "Alto Decorativo fondo 33cm 40cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 40, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 201, "Z2": 234, "Z3": 197, "Z4": 175, "Z5": 207, "Z6": 254, "Z7": 275, "Z8": 254, "Z9": 275, "Z10": 265, "Z11": 265, "Z12": 265}},
    {"reference": "7ADEC450", "name": "Alto Decorativo fondo 33cm 45cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 45, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 205, "Z2": 238, "Z3": 201, "Z4": 180, "Z5": 210, "Z6": 257, "Z7": 278, "Z8": 257, "Z9": 278, "Z10": 268, "Z11": 268, "Z12": 268}},
    {"reference": "7ADEC500", "name": "Alto Decorativo fondo 33cm 50cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 50, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 221, "Z2": 253, "Z3": 215, "Z4": 193, "Z5": 226, "Z6": 275, "Z7": 297, "Z8": 275, "Z9": 297, "Z10": 287, "Z11": 287, "Z12": 287}},
    {"reference": "7ADEC600", "name": "Alto Decorativo fondo 33cm 60cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 60, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 237, "Z2": 269, "Z3": 230, "Z4": 206, "Z5": 240, "Z6": 296, "Z7": 319, "Z8": 296, "Z9": 319, "Z10": 309, "Z11": 309, "Z12": 309}},
    {"reference": "7ADEC700", "name": "Alto Decorativo fondo 33cm 70cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 70, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 284, "Z2": 315, "Z3": 276, "Z4": 252, "Z5": 287, "Z6": 342, "Z7": 365, "Z8": 342, "Z9": 365, "Z10": 355, "Z11": 355, "Z12": 355}},
    {"reference": "7ADEC800", "name": "Alto Decorativo fondo 33cm 80cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 80, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 330, "Z2": 361, "Z3": 322, "Z4": 298, "Z5": 333, "Z6": 389, "Z7": 412, "Z8": 389, "Z9": 412, "Z10": 401, "Z11": 401, "Z12": 401}},
    {"reference": "7ADEC900", "name": "Alto Decorativo fondo 33cm 90cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 90, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 376, "Z2": 407, "Z3": 369, "Z4": 344, "Z5": 379, "Z6": 435, "Z7": 470, "Z8": 435, "Z9": 458, "Z10": 447, "Z11": 447, "Z12": 447}},
    
    # Alto Decorativo fondo 58cm (1 estante)
    {"reference": "7ADEC58400", "name": "Alto Decorativo fondo 58cm 40cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 40, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 239, "Z2": 279, "Z3": 235, "Z4": 209, "Z5": 246, "Z6": 302, "Z7": 341, "Z8": 302, "Z9": 341, "Z10": 315, "Z11": 315, "Z12": 315}},
    {"reference": "7ADEC58450", "name": "Alto Decorativo fondo 58cm 45cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 45, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 244, "Z2": 284, "Z3": 239, "Z4": 213, "Z5": 250, "Z6": 307, "Z7": 345, "Z8": 307, "Z9": 345, "Z10": 319, "Z11": 319, "Z12": 319}},
    {"reference": "7ADEC58500", "name": "Alto Decorativo fondo 58cm 50cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 50, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 263, "Z2": 301, "Z3": 255, "Z4": 230, "Z5": 268, "Z6": 328, "Z7": 368, "Z8": 328, "Z9": 368, "Z10": 341, "Z11": 341, "Z12": 341}},
    {"reference": "7ADEC58600", "name": "Alto Decorativo fondo 58cm 60cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 60, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 281, "Z2": 320, "Z3": 273, "Z4": 245, "Z5": 286, "Z6": 352, "Z7": 395, "Z8": 352, "Z9": 395, "Z10": 368, "Z11": 368, "Z12": 368}},
    {"reference": "7ADEC58700", "name": "Alto Decorativo fondo 58cm 70cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 70, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 337, "Z2": 375, "Z3": 329, "Z4": 299, "Z5": 341, "Z6": 406, "Z7": 449, "Z8": 406, "Z9": 449, "Z10": 422, "Z11": 422, "Z12": 422}},
    {"reference": "7ADEC58800", "name": "Alto Decorativo fondo 58cm 80cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 80, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 392, "Z2": 431, "Z3": 383, "Z4": 355, "Z5": 396, "Z6": 462, "Z7": 504, "Z8": 462, "Z9": 504, "Z10": 477, "Z11": 477, "Z12": 477}},
    {"reference": "7ADEC58900", "name": "Alto Decorativo fondo 58cm 90cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 90, "alto": 70, "fondo": 58, "sourcePage": 59,
     "zonePoints": {"Z1": 446, "Z2": 485, "Z3": 439, "Z4": 410, "Z5": 450, "Z6": 517, "Z7": 560, "Z8": 517, "Z9": 560, "Z10": 532, "Z11": 532, "Z12": 532}},
    
    # Alto botellero cuadros fondo 33cm (3 estantes)
    {"reference": "7ABOT150", "name": "Alto botellero cuadros fondo 33cm 15cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 15, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 209, "Z2": 232, "Z3": 205, "Z4": 188, "Z5": 212, "Z6": 240, "Z7": 264, "Z8": 240, "Z9": 264, "Z10": 252, "Z11": 252, "Z12": 252}},
    {"reference": "7ABOT300", "name": "Alto botellero cuadros fondo 33cm 30cm", "series": "ALTOS 70 DECORATIVOS", "ancho": 30, "alto": 70, "fondo": 33, "sourcePage": 59,
     "zonePoints": {"Z1": 270, "Z2": 302, "Z3": 263, "Z4": 237, "Z5": 273, "Z6": 326, "Z7": 361, "Z8": 326, "Z9": 361, "Z10": 342, "Z11": 342, "Z12": 342}},
]

def create_product_doc(prod_data):
    """Create a product document for MongoDB"""
    return {
        "id": f"prod-{uuid.uuid4().hex[:8]}",
        "code": prod_data["reference"],
        "reference": prod_data["reference"],
        "name": prod_data["name"],
        "category": "ALTOS",
        "series": prod_data["series"],
        "visualType": "standard",
        "width": prod_data["ancho"],
        "height": prod_data["alto"],
        "depth": prod_data["fondo"],
        "ancho": prod_data["ancho"],
        "alto": prod_data["alto"],
        "fondo": prod_data["fondo"],
        "manufacturer": "Zona Cocinas",
        "points": prod_data["zonePoints"]["Z1"],
        "zonePoints": prod_data["zonePoints"],
        "module": "montada",
        "sourceFile": "TARIFA-TECNICA-ZONACOCINAS.pdf",
        "sourcePage": prod_data["sourcePage"],
        "catalogId": "cat-m-base",
        "programa": "ESTÁNDAR",
        "tipo_mueble": "ALTOS"
    }

def main():
    # Get existing references
    existing_refs = set()
    for prod in db.products.find({}, {"reference": 1, "_id": 0}):
        if prod.get("reference"):
            existing_refs.add(prod["reference"])
    
    print(f"Productos existentes en DB: {len(existing_refs)}")
    
    # Track new references from these pages
    new_refs = []
    added_count = 0
    updated_count = 0
    
    for prod_data in products_data:
        ref = prod_data["reference"]
        new_refs.append(ref)
        
        if ref in existing_refs:
            # Update existing product
            result = db.products.update_one(
                {"reference": ref},
                {"$set": {
                    "name": prod_data["name"],
                    "series": prod_data["series"],
                    "zonePoints": prod_data["zonePoints"],
                    "ancho": prod_data["ancho"],
                    "alto": prod_data["alto"],
                    "fondo": prod_data["fondo"],
                    "width": prod_data["ancho"],
                    "height": prod_data["alto"],
                    "depth": prod_data["fondo"],
                    "sourcePage": prod_data["sourcePage"]
                }}
            )
            if result.modified_count > 0:
                updated_count += 1
        else:
            # Insert new product
            doc = create_product_doc(prod_data)
            db.products.insert_one(doc)
            added_count += 1
    
    print(f"\nResultados del procesamiento páginas 55-59:")
    print(f"  - Productos nuevos añadidos: {added_count}")
    print(f"  - Productos actualizados: {updated_count}")
    print(f"  - Total referencias procesadas: {len(new_refs)}")
    
    # Load existing valid_references.json if exists, or create new
    valid_refs_path = "/app/valid_references.json"
    existing_valid_refs = []
    if os.path.exists(valid_refs_path):
        with open(valid_refs_path, 'r') as f:
            existing_valid_refs = json.load(f)
    
    # Add new references
    all_refs = list(set(existing_valid_refs + new_refs))
    all_refs.sort()
    
    # Save updated valid_references.json
    with open(valid_refs_path, 'w') as f:
        json.dump(all_refs, f, indent=2)
    
    print(f"\nArchivo valid_references.json actualizado:")
    print(f"  - Referencias anteriores: {len(existing_valid_refs)}")
    print(f"  - Referencias nuevas añadidas: {len(new_refs)}")
    print(f"  - Total referencias válidas: {len(all_refs)}")
    
    # Final count
    final_count = db.products.count_documents({})
    print(f"\nTotal productos en base de datos: {final_count}")
    
    return new_refs

if __name__ == "__main__":
    main()
