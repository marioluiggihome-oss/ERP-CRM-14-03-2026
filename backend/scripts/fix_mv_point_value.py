#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Corrige el pointValue de la biblioteca MV a 3.33 EUR/punto (valor oficial MV)
si está mal seteado (p.ej. 1.0 por el valor por defecto antiguo).
"""
import os
from pymongo import MongoClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

MV_POINT_VALUE = 3.33

if __name__ == '__main__':
    mv = db.libraries.find_one({'code': 'MV'})
    if not mv:
        print("Biblioteca MV no encontrada, nada que corregir.")
    elif mv.get('pointValue') == MV_POINT_VALUE:
        print(f"Biblioteca MV ya tiene pointValue={MV_POINT_VALUE}, sin cambios.")
    else:
        result = db.libraries.update_one(
            {'code': 'MV'},
            {'$set': {'pointValue': MV_POINT_VALUE}}
        )
        print(f"pointValue MV corregido: {mv.get('pointValue')} -> {MV_POINT_VALUE} (modificados: {result.modified_count})")
