#!/usr/bin/env python3
"""
Process pages 230-234 of TARIFA-TECNICA-ZONACOCINAS
Columnas con horno y caceroleros - ALTO 220cm FONDO 58cm
"""

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")

# Products from pages 230-234
PRODUCTS_230_234 = [
    # ========== PAGE 230 - Columna 1 cacerolero ==========
    # Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta abatible
    {"reference": "22CH1G2CB1PABL600", "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta abatible 60cm", "zones": [603, 622, 656, 670, 717, 731, 770, 780, 811, 869, 900, 1028]},
    {"reference": "22CH1G2CB1PABL900", "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 1 puerta abatible 90cm", "zones": [723, 746, 788, 804, 861, 877, 924, 936, 973, 1043, 1080, 1234]},
    
    # Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta abatible
    {"reference": "22CH1G2CL1PABL600", "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta abatible 60cm", "zones": [684, 702, 737, 751, 798, 812, 852, 861, 891, 950, 982, 1109]},
    {"reference": "22CH1G2CL1PABL900", "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 1 puerta abatible 90cm", "zones": [820, 843, 885, 901, 958, 974, 1022, 1033, 1070, 1140, 1178, 1331]},
    
    # Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 2 puertas
    {"reference": "22CH1G2CB2P600", "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 2 puertas 60cm", "zones": [492, 515, 551, 551, 599, 659, 706, 717, 754, 820, 859, 1026]},
    {"reference": "22CH1G2CB2P900", "name": "Columna 1 cacerolero + 2 cajones Bax + horno 600mm + 2 puertas 90cm", "zones": [591, 617, 662, 662, 718, 791, 847, 861, 905, 984, 1031, 1231]},
    
    # Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 2 puertas
    {"reference": "22CH1G2CL2P600", "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 2 puertas 60cm", "zones": [574, 595, 632, 633, 679, 740, 788, 798, 836, 901, 940, 1108]},
    {"reference": "22CH1G2CL2P900", "name": "Columna 1 cacerolero + 2 cajones Lux + horno 600mm + 2 puertas 90cm", "zones": [689, 714, 759, 760, 815, 888, 945, 958, 1003, 1081, 1128, 1329]},
    
    # ========== PAGE 231 - Columna 2 caceroleros ==========
    # Columna 2 caceroleros + 1 cajon Bax + horno + 1 puerta
    {"reference": "22H2G1CB1P600", "name": "Columna 2 caceroleros + 1 cajón Bax + horno + 1 puerta 60cm", "zones": [475, 486, 518, 526, 568, 573, 608, 615, 643, 700, 726, 822]},
    
    # Columna 2 caceroleros + 1 cajon Lux + horno + 1 puerta
    {"reference": "22H2G1CL1P600", "name": "Columna 2 caceroleros + 1 cajón Lux + horno + 1 puerta 60cm", "zones": [561, 570, 602, 614, 657, 662, 696, 705, 732, 785, 811, 906]},
    
    # Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 1 puerta abatible
    {"reference": "22CH2G1CB1PABL600", "name": "Columna 2 caceroleros + 1 cajón Bax + horno 600mm + 1 puerta abatible 60cm", "zones": [606, 617, 649, 657, 699, 705, 739, 747, 774, 832, 857, 953]},
    {"reference": "22CH2G1CB1PABL900", "name": "Columna 2 caceroleros + 1 cajón Bax + horno 600mm + 1 puerta abatible 90cm", "zones": [721, 735, 772, 782, 832, 838, 880, 888, 921, 990, 1020, 1135]},
    
    # Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 1 puerta abatible
    {"reference": "22CH2G1CL1PABL600", "name": "Columna 2 caceroleros + 1 cajón Lux + horno 600mm + 1 puerta abatible 60cm", "zones": [692, 701, 733, 746, 789, 793, 827, 836, 863, 917, 942, 1037]},
    {"reference": "22CH2G1CL1PABL900", "name": "Columna 2 caceroleros + 1 cajón Lux + horno 600mm + 1 puerta abatible 90cm", "zones": [823, 835, 872, 887, 938, 943, 985, 995, 1027, 1091, 1121, 1235]},
    
    # ========== PAGE 232 - Columna 2 caceroleros (cont) ==========
    # Columna 2 caceroleros + 1 cajon Bax + horno 600mm + 2 puertas
    {"reference": "22CH2G1CB2P600", "name": "Columna 2 caceroleros + 1 cajón Bax + horno 600mm + 2 puertas 60cm", "zones": [504, 517, 550, 549, 592, 643, 685, 695, 729, 789, 822, 958]},
    {"reference": "22CH2G1CB2P900", "name": "Columna 2 caceroleros + 1 cajón Bax + horno 600mm + 2 puertas 90cm", "zones": [595, 610, 649, 648, 699, 758, 808, 820, 860, 930, 970, 1130]},
    
    # Columna 2 caceroleros + 1 cajon Lux + horno 600mm + 2 puertas
    {"reference": "22CH2G1CL2P600", "name": "Columna 2 caceroleros + 1 cajón Lux + horno 600mm + 2 puertas 60cm", "zones": [587, 600, 634, 633, 676, 727, 769, 779, 812, 873, 906, 1042]},
    {"reference": "22CH2G1CL2P900", "name": "Columna 2 caceroleros + 1 cajón Lux + horno 600mm + 2 puertas 90cm", "zones": [704, 719, 761, 760, 811, 872, 922, 935, 974, 1047, 1087, 1250]},
    
    # Columna 2 caceroleros Bax + horno 600mm + 1 puerta (Der/Izq)
    {"reference": "22CH2GB1P600", "name": "Columna 2 caceroleros Bax + horno 600mm + 1 puerta (Der/Izq) 60cm", "zones": [420, 437, 467, 469, 508, 538, 573, 582, 609, 617, 641, 738]},
    
    # Columna 2 caceroleros Lux + horno 600mm + 1 puerta (Der/Izq)
    {"reference": "22CH2GL1P600", "name": "Columna 2 caceroleros Lux + horno 600mm + 1 puerta (Der/Izq) 60cm", "zones": [477, 494, 525, 526, 566, 594, 630, 638, 667, 675, 698, 795]},
    
    # ========== PAGE 233 - Columna 2 caceroleros Bax/Lux ==========
    # Columna 2 caceroleros Bax + horno 600mm + 2 puertas
    {"reference": "22CH2GB2P600", "name": "Columna 2 caceroleros Bax + horno 600mm + 2 puertas 60cm", "zones": [446, 466, 499, 487, 527, 603, 646, 655, 690, 705, 736, 873]},
    {"reference": "22CH2GB2P900", "name": "Columna 2 caceroleros Bax + horno 600mm + 2 puertas 90cm", "zones": [536, 559, 599, 585, 633, 723, 775, 786, 828, 845, 883, 1047]},
    
    # Columna 2 caceroleros Lux + horno 600mm + 2 puertas
    {"reference": "22CH2GL2P600", "name": "Columna 2 caceroleros Lux + horno 600mm + 2 puertas 60cm", "zones": [504, 523, 557, 545, 584, 659, 702, 713, 747, 762, 793, 929]},
    {"reference": "22CH2GL2P900", "name": "Columna 2 caceroleros Lux + horno 600mm + 2 puertas 90cm", "zones": [605, 627, 668, 654, 701, 791, 843, 856, 896, 915, 951, 1115]},
    
    # Columna 1 puerta + horno + micro + 1 puerta (Der/Izq)
    {"reference": "22HM1P1P600", "name": "Columna 1 puerta + horno + micro + 1 puerta (Der/Izq) 60cm", "zones": [292, 302, 326, 320, 348, 353, 375, 380, 397, 424, 439, 499]},
    
    # Columna 1 puerta + horno + micro + 1 puerta abatible HK
    {"reference": "20HM1P1PABL600", "name": "Columna 1 puerta + horno + micro + 1 puerta abatible HK 60cm", "zones": [401, 412, 433, 428, 454, 466, 488, 494, 510, 521, 537, 596]},
    
    # ========== PAGE 234 ==========
    # Columna 2 puertas + horno + micro + 2 puertas
    {"reference": "22HM1P1PABL600", "name": "Columna 2 puertas + horno + micro + 2 puertas 60cm", "zones": [401, 412, 433, 428, 454, 466, 488, 494, 510, 521, 537, 596]},
    
    # Columna 4 cajones Bax + horno + micro + 1 puerta (Der/Izq)
    {"reference": "22HM4CB1P600", "name": "Columna 4 cajones Bax + horno + micro + 1 puerta (Der/Izq) 60cm", "zones": [499, 498, 527, 505, 537, 554, 582, 589, 611, 643, 658, 683]},
    
    # Columna 4 cajones Lux + horno + micro + 1 puerta (Der/Izq)
    {"reference": "22HM4CL1P600", "name": "Columna 4 cajones Lux + horno + micro + 1 puerta (Der/Izq) 60cm", "zones": [603, 603, 632, 610, 642, 659, 687, 693, 715, 747, 763, 788]},
    
    # Columna 4 cajones Bax + horno + micro + 2 puertas
    {"reference": "22HM4CB2P600", "name": "Columna 4 cajones Bax + horno + micro + 2 puertas 60cm", "zones": [524, 526, 558, 526, 558, 597, 629, 636, 662, 715, 740, 795]},
]

async def process_products():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    added = 0
    updated = 0
    skipped = 0
    
    for product in PRODUCTS_230_234:
        ref = product["reference"]
        
        # Check if exists
        existing = await db.products.find_one({"reference": ref})
        
        # Build zone points
        zone_points = {}
        for i, price in enumerate(product["zones"], 1):
            zone_points[f"Z{i}"] = price
        
        product_doc = {
            "reference": ref,
            "name": product["name"],
            "code": ref,
            "module": "montada",
            "points": product["zones"][0],  # Z1 as default price
            "zonePoints": zone_points,
            "category": "COLUMNAS",
            "subcategory": "Columnas Horno",
            "type": "columna_horno",
            "defaultWidth": 600 if "600" in ref else 900,
            "defaultHeight": 2200,
            "defaultDepth": 580,
            "hasLeftRight": "PABL" in ref or "P600" in ref or "P900" in ref,
            "drawerType": "Lux" if "CL" in ref or "GL" in ref else "Bax" if "CB" in ref or "GB" in ref else None,
            "numDoors": 2 if "2P" in ref else 1,
            "hasOven": True,
            "hasMicrowave": "HM" in ref,
        }
        
        if existing:
            await db.products.update_one(
                {"reference": ref},
                {"$set": product_doc}
            )
            updated += 1
            print(f"  Updated: {ref}")
        else:
            await db.products.insert_one(product_doc)
            added += 1
            print(f"  Added: {ref}")
    
    # Update valid_references.json
    try:
        with open("/app/valid_references.json", "r") as f:
            valid_refs = json.load(f)
    except:
        valid_refs = []
    
    new_refs = [p["reference"] for p in PRODUCTS_230_234]
    for ref in new_refs:
        if ref not in valid_refs:
            valid_refs.append(ref)
    
    with open("/app/valid_references.json", "w") as f:
        json.dump(sorted(valid_refs), f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Total references: {len(valid_refs)}")
    
    # Get total products count
    total = await db.products.count_documents({})
    print(f"Total products in DB: {total}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(process_products())
