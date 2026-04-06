#!/usr/bin/env python3
"""
Herramienta de sincronización de catálogo PDF vs MongoDB
"""
import json
import re
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Tuple

# Conectar a MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['luiggi_home']
products_collection = db['products']


def get_all_db_products() -> Dict[str, dict]:
    """Obtiene todos los productos de la BD indexados por código"""
    products = {}
    for doc in products_collection.find({}, {"_id": 0}):
        code = doc.get("code", "").strip().upper()
        if code:
            products[code] = doc
    return products


def normalize_code(code: str) -> str:
    """Normaliza un código de producto"""
    if not code:
        return ""
    # Eliminar espacios y convertir a mayúsculas
    return code.strip().upper()


def compare_products(pdf_products: List[dict], db_products: Dict[str, dict]) -> dict:
    """
    Compara productos del PDF con la BD
    Retorna un informe de discrepancias
    """
    report = {
        "missing_in_db": [],       # En PDF pero no en BD
        "extra_in_db": [],          # En BD pero no en PDF (podría ser correcto)
        "name_mismatch": [],        # Nombres diferentes
        "price_mismatch": [],       # Precios diferentes
        "exact_matches": 0,
        "total_pdf": len(pdf_products),
        "total_db": len(db_products),
        "timestamp": datetime.now().isoformat()
    }
    
    pdf_codes = set()
    
    for pdf_prod in pdf_products:
        code = normalize_code(pdf_prod.get("code", ""))
        if not code:
            continue
            
        pdf_codes.add(code)
        name_pdf = pdf_prod.get("name", "").strip()
        
        if code not in db_products:
            report["missing_in_db"].append({
                "code": code,
                "name": name_pdf,
                "category": pdf_prod.get("category", "")
            })
        else:
            db_prod = db_products[code]
            name_db = db_prod.get("name", "").strip()
            
            # Comparar nombres (permitiendo algunas variaciones)
            if name_pdf.lower() != name_db.lower():
                # Verificar si es una diferencia significativa
                if not names_are_similar(name_pdf, name_db):
                    report["name_mismatch"].append({
                        "code": code,
                        "name_pdf": name_pdf,
                        "name_db": name_db
                    })
            else:
                report["exact_matches"] += 1
    
    # Productos en BD que no están en PDF
    db_codes = set(db_products.keys())
    extra_codes = db_codes - pdf_codes
    for code in extra_codes:
        db_prod = db_products[code]
        report["extra_in_db"].append({
            "code": code,
            "name": db_prod.get("name", ""),
            "category": db_prod.get("category", "")
        })
    
    return report


def names_are_similar(name1: str, name2: str) -> bool:
    """
    Verifica si dos nombres son similares (permite pequeñas diferencias)
    """
    # Normalizar: minúsculas, eliminar espacios extra, eliminar caracteres especiales
    def normalize(s):
        s = s.lower()
        s = re.sub(r'\s+', ' ', s).strip()
        s = re.sub(r'[()/-]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    
    n1 = normalize(name1)
    n2 = normalize(name2)
    
    # Verificar si uno contiene al otro
    if n1 in n2 or n2 in n1:
        return True
    
    # Verificar similitud por palabras
    words1 = set(n1.split())
    words2 = set(n2.split())
    common = words1 & words2
    total = words1 | words2
    
    if len(total) > 0:
        similarity = len(common) / len(total)
        return similarity > 0.7
    
    return False


def print_report(report: dict):
    """Imprime el informe de manera legible"""
    print("\n" + "="*80)
    print("INFORME DE SINCRONIZACIÓN DE CATÁLOGO")
    print("="*80)
    print(f"Fecha: {report['timestamp']}")
    print(f"Total productos en PDF: {report['total_pdf']}")
    print(f"Total productos en BD: {report['total_db']}")
    print(f"Coincidencias exactas: {report['exact_matches']}")
    
    print("\n" + "-"*40)
    print(f"PRODUCTOS FALTANTES EN BD ({len(report['missing_in_db'])})")
    print("-"*40)
    for prod in report['missing_in_db'][:20]:  # Mostrar primeros 20
        print(f"  [{prod['code']}] {prod['name'][:50]}")
    if len(report['missing_in_db']) > 20:
        print(f"  ... y {len(report['missing_in_db']) - 20} más")
    
    print("\n" + "-"*40)
    print(f"DISCREPANCIAS EN NOMBRES ({len(report['name_mismatch'])})")
    print("-"*40)
    for item in report['name_mismatch'][:20]:
        print(f"  [{item['code']}]")
        print(f"    PDF: {item['name_pdf'][:60]}")
        print(f"    BD:  {item['name_db'][:60]}")
    if len(report['name_mismatch']) > 20:
        print(f"  ... y {len(report['name_mismatch']) - 20} más")
    
    print("\n" + "-"*40)
    print(f"PRODUCTOS EXTRA EN BD ({len(report['extra_in_db'])})")
    print("-"*40)
    for prod in report['extra_in_db'][:10]:
        print(f"  [{prod['code']}] {prod['name'][:50]}")
    if len(report['extra_in_db']) > 10:
        print(f"  ... y {len(report['extra_in_db']) - 10} más")
    
    print("\n" + "="*80)


def save_report(report: dict, filename: str = "/app/catalog_sync_report.json"):
    """Guarda el informe en un archivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nInforme guardado en: {filename}")


# Productos extraídos del PDF - Parte 1 (Bajos 70cm)
PDF_PRODUCTS_PART1 = [
    # Bajos 70cm Fondo Estándar
    {"code": "7B1P1CB300", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB350", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB400", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB450", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB500", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB600", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB700", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB800", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB900", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB1000", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1P1CB1200", "name": "Bajo 2 caceroleros 280mm + 1 cajón 140mm BAX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL300", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL350", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL400", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL450", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL500", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL600", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL700", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL800", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL900", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL1000", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B1G3CL1200", "name": "Bajo 1 cacerolero 280mm + 3 cajones 140mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CBX300", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX350", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX400", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX450", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX500", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX600", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX700", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX800", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX900", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX1000", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CBX1200", "name": "Bajo 4 cajones 175mm BAX", "category": "Bajos 70cm"},
    {"code": "7B4CLX300", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX350", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX400", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX450", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX500", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX600", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX700", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX800", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX900", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX1000", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    {"code": "7B4CLX1200", "name": "Bajo 4 cajones 175mm LUX", "category": "Bajos 70cm"},
    # Bajos 70cm Fondo 33cm
    {"code": "7B5CBX300", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX350", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX400", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX450", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX500", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX600", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX700", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX800", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX900", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX1000", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CBX1200", "name": "Bajo 5 cajones 200mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX300", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX350", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX400", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX450", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX500", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX600", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX700", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX800", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX900", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX1000", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B5CLX1200", "name": "Bajo 5 cajones 200mm LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX300", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX350", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX400", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX450", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX500", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX600", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CBX650", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón 140mm BAX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX300", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX350", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX400", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX450", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX500", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX600", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
    {"code": "7B1P1CLX650", "name": "Bajo 1 puerta (Derecha/Izquierda) + 1 cajón LUX fondo 330mm", "category": "Bajos 70cm Fondo 33cm"},
]

# Productos extraídos del PDF - Parte 2 (más bajos y decorativos)
PDF_PRODUCTS_PART2 = [
    {"code": "7B1G2CBX300", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX350", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX400", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX450", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX500", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX600", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX700", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX800", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX900", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX1000", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CBX1200", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX300", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX350", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX400", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX450", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX500", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX600", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX700", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX800", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX900", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX1000", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B1G2CLX1200", "name": "Bajo 1 cacerolero 350mm + 2 cajones 175mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX300", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX350", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX400", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX450", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX500", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX600", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX700", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX800", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX900", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX1000", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GBX1200", "name": "Bajo 2 caceroleros 350mm BAX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX300", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX350", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX400", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX450", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX500", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX600", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX700", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX800", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX900", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX1000", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7B2GLX1200", "name": "Bajo 2 caceroleros 350mm LUX fondo 330mm", "category": "Bajos"},
    {"code": "7BPM1GB600", "name": "Bajo 1 cacerolero 300 BAX + micro 400mm fondo 330", "category": "Bajos"},
    {"code": "7BPM1LB600", "name": "Bajo 1 cacerolero 300 LUX + micro 400mm fondo 330", "category": "Bajos"},
    {"code": "7BBOT150", "name": "Bajo botellero cuadros (3 estantes)", "category": "Bajos"},
    {"code": "7BBOT300", "name": "Bajo botellero cuadros (3 estantes)", "category": "Bajos"},
    {"code": "7BTER300", "name": "Bajo terminal abierto (1 estante)", "category": "Bajos"},
    {"code": "7BDEC150", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC200", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC300", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC350", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC400", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC450", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC500", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDEC600", "name": "Bajo decorativo fondo 580mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX150", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX200", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX300", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX350", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX400", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX450", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX500", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    {"code": "7BDECX600", "name": "Bajo decorativo fondo 330mm (1 estante)", "category": "Bajos"},
    # Bajos 80cm
    {"code": "8B1P300", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P350", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P400", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P450", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P500", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P600", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P650", "name": "Bajo 1 puerta (Derecha/Izquierda)", "category": "Bajos 80cm"},
    {"code": "8B1P1CB300", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB350", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB400", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB450", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB500", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB600", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CB650", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL300", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL350", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL400", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL450", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL500", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL600", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B1P1CL650", "name": "Bajo 1 puerta 640mm (Derecha/Izquierda) + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB600", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB700", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB800", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB900", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB1000", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB1200", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CB1300", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm BAX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL600", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL700", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL800", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL900", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL1000", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL1200", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B2P1CL1300", "name": "Bajo 2 puertas 640mm + 1 cajón 160mm LUX", "category": "Bajos 80cm"},
    {"code": "8B4CB300", "name": "Bajo 4 cajones 200mm BAX", "category": "Bajos 80cm"},
    {"code": "8B4CB350", "name": "Bajo 4 cajones 200mm BAX", "category": "Bajos 80cm"},
    {"code": "8B4CB400", "name": "Bajo 4 cajones 200mm BAX", "category": "Bajos 80cm"},
]

# Productos extraídos del PDF - Parte 3 (Altos Gola)
PDF_PRODUCTS_PART3 = [
    # Alto gola 1 puerta - Fondo Estándar
    {"code": "G45A1P350", "name": "Alto gola 1 puerta (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1P400", "name": "Alto gola 1 puerta (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1P450", "name": "Alto gola 1 puerta (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1P500", "name": "Alto gola 1 puerta (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1P600", "name": "Alto gola 1 puerta (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    # Alto gola 2 puertas
    {"code": "G45A2P600", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2P700", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2P800", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2P900", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2P1000", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2P1200", "name": "Alto gola 2 puertas - Fondo Estándar", "category": "Altos Gola"},
    # Alto gola 1 Vitrina
    {"code": "G45A1V350", "name": "Alto gola 1 Vitrina (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1V400", "name": "Alto gola 1 Vitrina (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1V450", "name": "Alto gola 1 Vitrina (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1V500", "name": "Alto gola 1 Vitrina (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A1V600", "name": "Alto gola 1 Vitrina (Derecha/Izquierda) - Fondo Estándar", "category": "Altos Gola"},
    # Alto gola 2 Vitrinas
    {"code": "G45A2V600", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2V700", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2V800", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2V900", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2V1000", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45A2V1200", "name": "Alto gola 2 Vitrinas - Fondo Estándar", "category": "Altos Gola"},
    # Alto gola abatible HK-TOP
    {"code": "G45APABL350", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL400", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL450", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL500", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL600", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL700", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL800", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL900", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL1000", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APABL1200", "name": "Alto gola 1 puerta abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    # Alto gola vitrina abatible HK-TOP
    {"code": "G45AVABL350", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL400", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL450", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL500", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL600", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL700", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL800", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45AVABL900", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APVBL1000", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    {"code": "G45APVBL1200", "name": "Alto gola 1 vitrina abatible HK-TOP - Fondo Estándar", "category": "Altos Gola"},
    # Columnas gola
    {"code": "GV22CD1P300", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P350", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P400", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P500", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P600", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P450", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    {"code": "GV22CD1P650", "name": "Columna gola vertical 1 puerta (Derecha/Izquierda)", "category": "Columnas Gola"},
    # Columna 2 vitrinas
    {"code": "G24CD2V2V600", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V700", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V800", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V1000", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V1200", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V900", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    {"code": "G24CD2V2V1300", "name": "Columna gola 2 vitrinas", "category": "Columnas Gola"},
    # Columna con horno
    {"code": "G24CH2GB1P600", "name": "Columna gola 2 caceroleros BAX + horno + 1 puerta push incluido", "category": "Columnas Gola"},
    {"code": "G24CH2GB2P600", "name": "Columna gola 2 caceroleros BAX + horno + 2 puertas push incluidos", "category": "Columnas Gola"},
    {"code": "G24CH2GB2P900", "name": "Columna gola 2 caceroleros BAX + horno + 2 puertas push incluidos", "category": "Columnas Gola"},
]


def main():
    """Función principal"""
    print("Cargando productos de la base de datos...")
    db_products = get_all_db_products()
    print(f"Se encontraron {len(db_products)} productos en la BD")
    
    # Combinar todos los productos del PDF
    all_pdf_products = PDF_PRODUCTS_PART1 + PDF_PRODUCTS_PART2 + PDF_PRODUCTS_PART3
    print(f"Se tienen {len(all_pdf_products)} productos del PDF")
    
    # Comparar
    print("\nComparando productos...")
    report = compare_products(all_pdf_products, db_products)
    
    # Mostrar informe
    print_report(report)
    
    # Guardar informe
    save_report(report)
    
    return report


if __name__ == "__main__":
    main()
