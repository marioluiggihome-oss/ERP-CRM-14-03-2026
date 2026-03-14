"""
Datos de la Tarifa MV con estructura correcta
Sistema de TARIFAS T1-T21 con matriz de precios por ALTO x ANCHO
"""

# TARIFA 1 - Precios base
# Formato: {codigo_ancho: {alto: precio}}

TARIFA_1 = {
    # ===========================================
    # PUERTAS - Precios por ALTO (cm) x ANCHO
    # ===========================================
    "PUERTAS": {
        "P25": {70: 10, 90: 13},
        "P30": {14: 4, 28: 5, 40: 9, 56: 10, 70: 11, 90: 14, 127: 16, 147: 19},
        "P35": {14: 4, 28: 6, 40: 10, 56: 11, 70: 12, 90: 15, 127: 17, 147: 20},
        "P40": {14: 4, 28: 6, 40: 10, 56: 11, 70: 13, 90: 15, 127: 19, 147: 21},
        "P45": {14: 4, 28: 7, 40: 10, 56: 11, 70: 13, 90: 16, 127: 19, 147: 22},
        "P50": {14: 4, 28: 8, 40: 11, 56: 13, 70: 14, 90: 17, 127: 20, 147: 23},
        "P60": {14: 4, 56: 13, 70: 16, 90: 19, 127: 22, 147: 26},
    },
    
    # VITRINA
    "VITRINA": {
        "PV30": {28: 20, 40: 31, 70: 43, 90: 49, 127: 68, 147: 77},
        "PV35": {28: 22, 40: 36, 70: 43, 90: 52, 127: 72, 147: 82},
        "PV40": {28: 23, 40: 37, 70: 45, 90: 54, 127: 76, 147: 87},
        "PV45": {28: 24, 40: 38, 70: 47, 90: 57, 127: 81, 147: 92},
        "PV50": {28: 25, 40: 40, 70: 49, 90: 59, 127: 85, 147: 97},
        "PV60": {28: 28, 40: 42, 70: 54, 90: 65, 127: 89, 147: 118},
    },
    
    # REJILLA
    "REJILLA": {
        "PR30": {70: 41, 90: 51, 127: 55, 147: 63},
        "PR35": {70: 45, 90: 55, 127: 60, 147: 69},
        "PR40": {70: 48, 90: 60, 127: 67, 147: 76},
        "PR45": {70: 51, 90: 65, 127: 71, 147: 82},
        "PR50": {70: 56, 90: 68, 127: 78, 147: 88},
        "PR60": {70: 63, 90: 78, 127: 89, 147: 109},
    },
}

# ===========================================
# PRODUCTOS MV con precios de TARIFA 1
# Formato simplificado para importación
# ===========================================

MV_PRODUCTS_T1 = {
    # BAJO (de análisis de imagen TARIFA 4, ajustando a T1)
    "B25D/I": {"name": "BAJO 25", "category": "BAJO", "T1": 41},
    "B30D/I": {"name": "BAJO 30", "category": "BAJO", "T1": 42},
    "B35D/I": {"name": "BAJO 35", "category": "BAJO", "T1": 43},
    "B40D/I": {"name": "BAJO 40", "category": "BAJO", "T1": 44},
    "B45D/I": {"name": "BAJO 45", "category": "BAJO", "T1": 45},
    "B50D/I": {"name": "BAJO 50", "category": "BAJO", "T1": 50},
    "B60D/I": {"name": "BAJO 60", "category": "BAJO", "T1": 55},
    "B60": {"name": "BAJO 60 2P", "category": "BAJO", "T1": 62},
    "B70": {"name": "BAJO 70", "category": "BAJO", "T1": 65},
    "B80": {"name": "BAJO 80", "category": "BAJO", "T1": 68},
    "B90": {"name": "BAJO 90", "category": "BAJO", "T1": 72},
    "B100": {"name": "BAJO 100", "category": "BAJO", "T1": 78},
    
    # BAJO FREGADERO
    "BF45D/I": {"name": "BAJO FREGADERO 45", "category": "BAJO_FREGADERO", "T1": 44},
    "BF50D/I": {"name": "BAJO FREGADERO 50", "category": "BAJO_FREGADERO", "T1": 45},
    "BF55D/I": {"name": "BAJO FREGADERO 55", "category": "BAJO_FREGADERO", "T1": 47},
    "BF60D/I": {"name": "BAJO FREGADERO 60", "category": "BAJO_FREGADERO", "T1": 53},
    "BF70": {"name": "BAJO FREGADERO 70", "category": "BAJO_FREGADERO", "T1": 60},
    "BF80": {"name": "BAJO FREGADERO 80", "category": "BAJO_FREGADERO", "T1": 64},
    "BF90": {"name": "BAJO FREGADERO 90", "category": "BAJO_FREGADERO", "T1": 70},
    "BF100": {"name": "BAJO FREGADERO 100", "category": "BAJO_FREGADERO", "T1": 73},
    "BF120": {"name": "BAJO FREGADERO 120", "category": "BAJO_FREGADERO", "T1": 80},
    
    # BAJO PUERTA Y CAJON
    "BPC30D/I": {"name": "BAJO PUERTA CAJON 30", "category": "BAJO_PUERTA_CAJON", "T1": 72},
    "BPC35D/I": {"name": "BAJO PUERTA CAJON 35", "category": "BAJO_PUERTA_CAJON", "T1": 75},
    "BPC40D/I": {"name": "BAJO PUERTA CAJON 40", "category": "BAJO_PUERTA_CAJON", "T1": 77},
    "BPC45D/I": {"name": "BAJO PUERTA CAJON 45", "category": "BAJO_PUERTA_CAJON", "T1": 80},
    "BPC50D/I": {"name": "BAJO PUERTA CAJON 50", "category": "BAJO_PUERTA_CAJON", "T1": 83},
    "BPC60D/I": {"name": "BAJO PUERTA CAJON 60", "category": "BAJO_PUERTA_CAJON", "T1": 88},
    "BPC60": {"name": "BAJO PUERTA CAJON 60 2P", "category": "BAJO_PUERTA_CAJON", "T1": 123},
    "BPC70": {"name": "BAJO PUERTA CAJON 70", "category": "BAJO_PUERTA_CAJON", "T1": 128},
    "BPC80": {"name": "BAJO PUERTA CAJON 80", "category": "BAJO_PUERTA_CAJON", "T1": 133},
    "BPC90": {"name": "BAJO PUERTA CAJON 90", "category": "BAJO_PUERTA_CAJON", "T1": 140},
    "BPC100": {"name": "BAJO PUERTA CAJON 100", "category": "BAJO_PUERTA_CAJON", "T1": 146},
    
    # BAJO 5 CAJONES
    "BC30": {"name": "BAJO 5 CAJONES 30", "category": "BAJO_CAJONES", "T1": 163},
    "BC35": {"name": "BAJO 5 CAJONES 35", "category": "BAJO_CAJONES", "T1": 167},
    "BC40": {"name": "BAJO 5 CAJONES 40", "category": "BAJO_CAJONES", "T1": 170},
    "BC45": {"name": "BAJO 5 CAJONES 45", "category": "BAJO_CAJONES", "T1": 176},
    "BC50": {"name": "BAJO 5 CAJONES 50", "category": "BAJO_CAJONES", "T1": 182},
    "BC60": {"name": "BAJO 5 CAJONES 60", "category": "BAJO_CAJONES", "T1": 186},
    "BC70": {"name": "BAJO 5 CAJONES 70", "category": "BAJO_CAJONES", "T1": 203},
    "BC80": {"name": "BAJO 5 CAJONES 80", "category": "BAJO_CAJONES", "T1": 233},
    "BC90": {"name": "BAJO 5 CAJONES 90", "category": "BAJO_CAJONES", "T1": 243},
    
    # BAJO 3 CAJONES + 1 GAVETA
    "BCG30": {"name": "BAJO 3CAJ+1GAV 30", "category": "BAJO_CAJ_GAV", "T1": 137},
    "BCG35": {"name": "BAJO 3CAJ+1GAV 35", "category": "BAJO_CAJ_GAV", "T1": 140},
    "BCG40": {"name": "BAJO 3CAJ+1GAV 40", "category": "BAJO_CAJ_GAV", "T1": 143},
    "BCG45": {"name": "BAJO 3CAJ+1GAV 45", "category": "BAJO_CAJ_GAV", "T1": 148},
    "BCG50": {"name": "BAJO 3CAJ+1GAV 50", "category": "BAJO_CAJ_GAV", "T1": 152},
    "BCG60": {"name": "BAJO 3CAJ+1GAV 60", "category": "BAJO_CAJ_GAV", "T1": 157},
    "BCG70": {"name": "BAJO 3CAJ+1GAV 70", "category": "BAJO_CAJ_GAV", "T1": 197},
    "BCG80": {"name": "BAJO 3CAJ+1GAV 80", "category": "BAJO_CAJ_GAV", "T1": 201},
    "BCG90": {"name": "BAJO 3CAJ+1GAV 90", "category": "BAJO_CAJ_GAV", "T1": 205},
    
    # BAJO 2 GAVETAS + 1 CAJON
    "BGC30": {"name": "BAJO 2GAV+1CAJ 30", "category": "BAJO_GAV_CAJ", "T1": 111},
    "BGC35": {"name": "BAJO 2GAV+1CAJ 35", "category": "BAJO_GAV_CAJ", "T1": 115},
    "BGC40": {"name": "BAJO 2GAV+1CAJ 40", "category": "BAJO_GAV_CAJ", "T1": 116},
    "BGC45": {"name": "BAJO 2GAV+1CAJ 45", "category": "BAJO_GAV_CAJ", "T1": 120},
    "BGC50": {"name": "BAJO 2GAV+1CAJ 50", "category": "BAJO_GAV_CAJ", "T1": 125},
    "BGC60": {"name": "BAJO 2GAV+1CAJ 60", "category": "BAJO_GAV_CAJ", "T1": 128},
    "BGC70": {"name": "BAJO 2GAV+1CAJ 70", "category": "BAJO_GAV_CAJ", "T1": 160},
    "BGC80": {"name": "BAJO 2GAV+1CAJ 80", "category": "BAJO_GAV_CAJ", "T1": 164},
    "BGC90": {"name": "BAJO 2GAV+1CAJ 90", "category": "BAJO_GAV_CAJ", "T1": 168},
    
    # BAJO 2 CAJONES + 1 GAVETA + 1 FRENTE
    "BCGF60": {"name": "BAJO 2CAJ+1GAV+FRENTE 60", "category": "BAJO_CAJ_GAV_FRENTE", "T1": 136},
    "BCGF70": {"name": "BAJO 2CAJ+1GAV+FRENTE 70", "category": "BAJO_CAJ_GAV_FRENTE", "T1": 153},
    "BCGF80": {"name": "BAJO 2CAJ+1GAV+FRENTE 80", "category": "BAJO_CAJ_GAV_FRENTE", "T1": 173},
    "BCGF90": {"name": "BAJO 2CAJ+1GAV+FRENTE 90", "category": "BAJO_CAJ_GAV_FRENTE", "T1": 189},
    
    # BAJO 2 GAVETAS + 1 FRENTE
    "BGF60": {"name": "BAJO 2GAV+FRENTE 60", "category": "BAJO_GAV_FRENTE", "T1": 104},
    "BGF70": {"name": "BAJO 2GAV+FRENTE 70", "category": "BAJO_GAV_FRENTE", "T1": 119},
    "BGF80": {"name": "BAJO 2GAV+FRENTE 80", "category": "BAJO_GAV_FRENTE", "T1": 138},
    "BGF90": {"name": "BAJO 2GAV+FRENTE 90", "category": "BAJO_GAV_FRENTE", "T1": 139},
    "BGF120": {"name": "BAJO 2GAV+FRENTE 120", "category": "BAJO_GAV_FRENTE", "T1": 163},
    
    # BAJO HORNO
    "BH60": {"name": "BAJO HORNO 60", "category": "BAJO_HORNO", "T1": 38},
    "BHC60": {"name": "BAJO HORNO CAJON 60", "category": "BAJO_HORNO", "T1": 46},
    "BHZ60": {"name": "BAJO HORNO ZOCALO 60", "category": "BAJO_HORNO", "T1": 73},
    "BHG60": {"name": "BAJO HORNO GAVETA 60", "category": "BAJO_HORNO", "T1": 75},
    
    # BAJO RINCON CIEGO
    "BR90D/I": {"name": "BAJO RINCON 90 PTA30", "category": "BAJO_RINCON", "T1": 64},
    "BR95D/I": {"name": "BAJO RINCON 95 PTA35", "category": "BAJO_RINCON", "T1": 66},
    "BR100D/I": {"name": "BAJO RINCON 100 PTA40", "category": "BAJO_RINCON", "T1": 67},
    "BR105D/I": {"name": "BAJO RINCON 105 PTA45", "category": "BAJO_RINCON", "T1": 72},
    "BR110D/I": {"name": "BAJO RINCON 110 PTA50", "category": "BAJO_RINCON", "T1": 75},
    
    # BAJO RINCON ESCUADRA
    "BRI95D/I": {"name": "BAJO RINCON INDEP 95x95", "category": "BAJO_RINCON_ESC", "T1": 91},
    "BRU95D/I": {"name": "BAJO RINCON UNIDO 95x95", "category": "BAJO_RINCON_ESC", "T1": 89},
    
    # BAJO TERMINAL
    "BT30D/I": {"name": "BAJO TERMINAL 30", "category": "BAJO_TERMINAL", "T1": 47},
    "BTS30D/I": {"name": "BAJO TERMINAL SUELO 30", "category": "BAJO_TERMINAL", "T1": 51},
    "BTZ30D/I": {"name": "BAJO TERMINAL ZOCALO 30", "category": "BAJO_TERMINAL", "T1": 62},
    "BTP33D/I": {"name": "BAJO TERMINAL PUERTA 33", "category": "BAJO_TERMINAL", "T1": 73},
    
    # ===========================================
    # ALTO
    # ===========================================
    "A25D/I": {"name": "ALTO 25", "category": "ALTO", "T1": 39},
    "A30D/I": {"name": "ALTO 30", "category": "ALTO", "T1": 41},
    "A35D/I": {"name": "ALTO 35", "category": "ALTO", "T1": 43},
    "A40D/I": {"name": "ALTO 40", "category": "ALTO", "T1": 45},
    "A45D/I": {"name": "ALTO 45", "category": "ALTO", "T1": 48},
    "A50D/I": {"name": "ALTO 50", "category": "ALTO", "T1": 51},
    "A60D/I": {"name": "ALTO 60", "category": "ALTO", "T1": 56},
    "A60": {"name": "ALTO 60 2P", "category": "ALTO", "T1": 64},
    "A70": {"name": "ALTO 70", "category": "ALTO", "T1": 69},
    "A80": {"name": "ALTO 80", "category": "ALTO", "T1": 74},
    "A90": {"name": "ALTO 90", "category": "ALTO", "T1": 79},
    "A100": {"name": "ALTO 100", "category": "ALTO", "T1": 85},
    
    # ALTO VITRINA
    "AV30D/I": {"name": "ALTO VITRINA 30", "category": "ALTO_VITRINA", "T1": 48},
    "AV35D/I": {"name": "ALTO VITRINA 35", "category": "ALTO_VITRINA", "T1": 53},
    "AV40D/I": {"name": "ALTO VITRINA 40", "category": "ALTO_VITRINA", "T1": 56},
    "AV45D/I": {"name": "ALTO VITRINA 45", "category": "ALTO_VITRINA", "T1": 60},
    "AV50D/I": {"name": "ALTO VITRINA 50", "category": "ALTO_VITRINA", "T1": 64},
    "AV60D/I": {"name": "ALTO VITRINA 60", "category": "ALTO_VITRINA", "T1": 71},
    "AV60": {"name": "ALTO VITRINA 60 2P", "category": "ALTO_VITRINA", "T1": 80},
    "AV70": {"name": "ALTO VITRINA 70", "category": "ALTO_VITRINA", "T1": 87},
    "AV80": {"name": "ALTO VITRINA 80", "category": "ALTO_VITRINA", "T1": 94},
    "AV90": {"name": "ALTO VITRINA 90", "category": "ALTO_VITRINA", "T1": 101},
    "AV100": {"name": "ALTO VITRINA 100", "category": "ALTO_VITRINA", "T1": 109},
    
    # ALTO ESCURREPLATOS
    "AE45D/I": {"name": "ALTO ESCURREPLATOS 45", "category": "ALTO_ESCURREPLATOS", "T1": 87},
    "AE50D/I": {"name": "ALTO ESCURREPLATOS 50", "category": "ALTO_ESCURREPLATOS", "T1": 93},
    "AE60D/I": {"name": "ALTO ESCURREPLATOS 60", "category": "ALTO_ESCURREPLATOS", "T1": 105},
    "AE60": {"name": "ALTO ESCURREPLATOS 60 2P", "category": "ALTO_ESCURREPLATOS", "T1": 119},
    "AE70": {"name": "ALTO ESCURREPLATOS 70", "category": "ALTO_ESCURREPLATOS", "T1": 129},
    "AE80": {"name": "ALTO ESCURREPLATOS 80", "category": "ALTO_ESCURREPLATOS", "T1": 139},
    "AE90": {"name": "ALTO ESCURREPLATOS 90", "category": "ALTO_ESCURREPLATOS", "T1": 149},
    "AE100": {"name": "ALTO ESCURREPLATOS 100", "category": "ALTO_ESCURREPLATOS", "T1": 160},
    
    # ALTO MICROONDAS
    "AM60D/I": {"name": "ALTO MICROONDAS 60", "category": "ALTO_MICROONDAS", "T1": 66},
    "AM60": {"name": "ALTO MICROONDAS 60 2P", "category": "ALTO_MICROONDAS", "T1": 94},
    "AMF60D/I": {"name": "ALTO MICROONDAS FONDO 60", "category": "ALTO_MICROONDAS", "T1": 78},
    "AMF60": {"name": "ALTO MICROONDAS FONDO 60 2P", "category": "ALTO_MICROONDAS", "T1": 100},
    
    # ALTO CALENTADOR
    "ACA45D/I": {"name": "ALTO CALENTADOR 45", "category": "ALTO_CALENTADOR", "T1": 75},
    "ACA50D/I": {"name": "ALTO CALENTADOR 50", "category": "ALTO_CALENTADOR", "T1": 80},
    "ACA60D/I": {"name": "ALTO CALENTADOR 60", "category": "ALTO_CALENTADOR", "T1": 91},
    "ACA60": {"name": "ALTO CALENTADOR 60 2P", "category": "ALTO_CALENTADOR", "T1": 105},
    
    # ALTO CALDERA
    "ACC60D/I": {"name": "ALTO CALDERA 60", "category": "ALTO_CALDERA", "T1": 92},
    "ACC60": {"name": "ALTO CALDERA 60 2P", "category": "ALTO_CALDERA", "T1": 113},
    
    # ALTO SOBREFRIGO
    "ASF60D/I": {"name": "ALTO SOBREFRIGO 60", "category": "ALTO_SOBREFRIGO", "T1": 52},
    "ASF60": {"name": "ALTO SOBREFRIGO 60 2P", "category": "ALTO_SOBREFRIGO", "T1": 60},
    
    # ALTO RINCON
    "AR60D/I": {"name": "ALTO RINCON 60", "category": "ALTO_RINCON", "T1": 74},
    "AR65D/I": {"name": "ALTO RINCON 65", "category": "ALTO_RINCON", "T1": 77},
    "ARI65D/I": {"name": "ALTO RINCON INDEP 65", "category": "ALTO_RINCON", "T1": 85},
    "ARU65D/I": {"name": "ALTO RINCON UNIDO 65", "category": "ALTO_RINCON", "T1": 88},
    "ARC63D/I": {"name": "ALTO RINCON CHAFLAN 63", "category": "ALTO_RINCON", "T1": 88},
    
    # ALTO CAMPANA
    "ASC60D/I": {"name": "ALTO CAMPANA 60", "category": "ALTO_CAMPANA", "T1": 62},
    "ASC60": {"name": "ALTO CAMPANA 60 2P", "category": "ALTO_CAMPANA", "T1": 60},
    "ASCE60D/I": {"name": "ALTO CAMPANA EXTRAPLANA 60", "category": "ALTO_CAMPANA", "T1": 31},
    "ASCE60": {"name": "ALTO CAMPANA EXTRAPLANA 60 2P", "category": "ALTO_CAMPANA", "T1": 47},
    "ASCE90": {"name": "ALTO CAMPANA EXTRAPLANA 90", "category": "ALTO_CAMPANA", "T1": 37},
    
    # ALTO DECORATIVO
    "AD40": {"name": "ALTO DECORATIVO 40", "category": "ALTO_DECORATIVO", "T1": 80},
    "AD45": {"name": "ALTO DECORATIVO 45", "category": "ALTO_DECORATIVO", "T1": 98},
    "AD50": {"name": "ALTO DECORATIVO 50", "category": "ALTO_DECORATIVO", "T1": 105},
    "AD60": {"name": "ALTO DECORATIVO 60", "category": "ALTO_DECORATIVO", "T1": 125},
    "AD70": {"name": "ALTO DECORATIVO 70", "category": "ALTO_DECORATIVO", "T1": 127},
    "AD80": {"name": "ALTO DECORATIVO 80", "category": "ALTO_DECORATIVO", "T1": 143},
    "AD90": {"name": "ALTO DECORATIVO 90", "category": "ALTO_DECORATIVO", "T1": 154},
    "AD100": {"name": "ALTO DECORATIVO 100", "category": "ALTO_DECORATIVO", "T1": 169},
    
    # ALTO TERMINAL
    "AT30D/I": {"name": "ALTO TERMINAL 30", "category": "ALTO_TERMINAL", "T1": 45},
    "ATP33D/I": {"name": "ALTO TERMINAL PUERTA 33", "category": "ALTO_TERMINAL", "T1": 51},
    
    # ===========================================
    # COLUMNA
    # ===========================================
    "CD30D/I": {"name": "COLUMNA DESPENSERO 30", "category": "COLUMNA_DESPENSERO", "T1": 116},
    "CD35D/I": {"name": "COLUMNA DESPENSERO 35", "category": "COLUMNA_DESPENSERO", "T1": 122},
    "CD40D/I": {"name": "COLUMNA DESPENSERO 40", "category": "COLUMNA_DESPENSERO", "T1": 128},
    "CD45D/I": {"name": "COLUMNA DESPENSERO 45", "category": "COLUMNA_DESPENSERO", "T1": 134},
    "CD50D/I": {"name": "COLUMNA DESPENSERO 50", "category": "COLUMNA_DESPENSERO", "T1": 140},
    "CD60D/I": {"name": "COLUMNA DESPENSERO 60", "category": "COLUMNA_DESPENSERO", "T1": 152},
    "CD60": {"name": "COLUMNA DESPENSERO 60 2P", "category": "COLUMNA_DESPENSERO", "T1": 149},
    "CD70": {"name": "COLUMNA DESPENSERO 70", "category": "COLUMNA_DESPENSERO", "T1": 163},
    "CD80": {"name": "COLUMNA DESPENSERO 80", "category": "COLUMNA_DESPENSERO", "T1": 176},
    "CD90": {"name": "COLUMNA DESPENSERO 90", "category": "COLUMNA_DESPENSERO", "T1": 190},
    
    # COLUMNA ESCOBERO
    "CE60D/I": {"name": "COLUMNA ESCOBERO 60", "category": "COLUMNA_ESCOBERO", "T1": 91},
    "CE60": {"name": "COLUMNA ESCOBERO 60 2P", "category": "COLUMNA_ESCOBERO", "T1": 104},
    
    # COLUMNA HORNO
    "CH60D/I": {"name": "COLUMNA HORNO 60", "category": "COLUMNA_HORNO", "T1": 138},
    "CH60": {"name": "COLUMNA HORNO 60 2P", "category": "COLUMNA_HORNO", "T1": 230},
    "CHPC60D/I": {"name": "COLUMNA HORNO PTA+CAJ 60", "category": "COLUMNA_HORNO", "T1": 239},
    "CHPC60": {"name": "COLUMNA HORNO PTA+CAJ 60 2P", "category": "COLUMNA_HORNO", "T1": 269},
    "CHGC60D/I": {"name": "COLUMNA HORNO GAV+CAJ 60", "category": "COLUMNA_HORNO", "T1": 251},
    "CHGC60": {"name": "COLUMNA HORNO GAV+CAJ 60 2P", "category": "COLUMNA_HORNO", "T1": 281},
    "CHC60D/I": {"name": "COLUMNA HORNO CAJONES 60", "category": "COLUMNA_HORNO", "T1": 268},
    "CHC60": {"name": "COLUMNA HORNO CAJONES 60 2P", "category": "COLUMNA_HORNO", "T1": 298},
    
    # COLUMNA HORNO + MICRO
    "CHM60D/I": {"name": "COLUMNA HORNO+MICRO 60", "category": "COLUMNA_HORNO_MICRO", "T1": 212},
    "CHM60": {"name": "COLUMNA HORNO+MICRO 60 2P", "category": "COLUMNA_HORNO_MICRO", "T1": 242},
    "CHMG60D/I": {"name": "COLUMNA HORNO+MICRO GAV 60", "category": "COLUMNA_HORNO_MICRO", "T1": 225},
    "CHMG60": {"name": "COLUMNA HORNO+MICRO GAV 60 2P", "category": "COLUMNA_HORNO_MICRO", "T1": 255},
    "CHMC60D/I": {"name": "COLUMNA HORNO+MICRO CAJ 60", "category": "COLUMNA_HORNO_MICRO", "T1": 247},
    "CHMC60": {"name": "COLUMNA HORNO+MICRO CAJ 60 2P", "category": "COLUMNA_HORNO_MICRO", "T1": 277},
    "CHMCG60D/I": {"name": "COLUMNA HORNO+MICRO CAJ+GAV 60", "category": "COLUMNA_HORNO_MICRO", "T1": 260},
    "CHMCG60": {"name": "COLUMNA HORNO+MICRO CAJ+GAV 60 2P", "category": "COLUMNA_HORNO_MICRO", "T1": 290},
    
    # COLUMNA FRIGO
    "CF60D/I": {"name": "COLUMNA FRIGO 60", "category": "COLUMNA_FRIGO", "T1": 160},
    "CF60": {"name": "COLUMNA FRIGO 60 2P", "category": "COLUMNA_FRIGO", "T1": 173},
    "CFA60D/I": {"name": "COLUMNA FRIGO ABATIBLE 60", "category": "COLUMNA_FRIGO", "T1": 182},
    "CFA60": {"name": "COLUMNA FRIGO ABATIBLE 60 2P", "category": "COLUMNA_FRIGO", "T1": 190},
    "CFF60D/I": {"name": "COLUMNA FRIGO FREE 60", "category": "COLUMNA_FRIGO", "T1": 198},
    "CFF60": {"name": "COLUMNA FRIGO FREE 60 2P", "category": "COLUMNA_FRIGO", "T1": 210},
    
    # ===========================================
    # MEDIACOLUMNA
    # ===========================================
    "M30D/I": {"name": "MEDIACOLUMNA 30", "category": "MEDIACOLUMNA", "T1": 69},
    "M35D/I": {"name": "MEDIACOLUMNA 35", "category": "MEDIACOLUMNA", "T1": 74},
    "M40D/I": {"name": "MEDIACOLUMNA 40", "category": "MEDIACOLUMNA", "T1": 78},
    "M45D/I": {"name": "MEDIACOLUMNA 45", "category": "MEDIACOLUMNA", "T1": 82},
    "M50D/I": {"name": "MEDIACOLUMNA 50", "category": "MEDIACOLUMNA", "T1": 86},
    "M60D/I": {"name": "MEDIACOLUMNA 60", "category": "MEDIACOLUMNA", "T1": 95},
    "M60": {"name": "MEDIACOLUMNA 60 2P", "category": "MEDIACOLUMNA", "T1": 91},
    
    # MEDIACOLUMNA VITRINA
    "MV30D/I": {"name": "MEDIACOLUMNA VIT 30", "category": "MEDIACOLUMNA_VITRINA", "T1": 91},
    "MV35D/I": {"name": "MEDIACOLUMNA VIT 35", "category": "MEDIACOLUMNA_VITRINA", "T1": 95},
    "MV40D/I": {"name": "MEDIACOLUMNA VIT 40", "category": "MEDIACOLUMNA_VITRINA", "T1": 100},
    "MV45D/I": {"name": "MEDIACOLUMNA VIT 45", "category": "MEDIACOLUMNA_VITRINA", "T1": 104},
    "MV50D/I": {"name": "MEDIACOLUMNA VIT 50", "category": "MEDIACOLUMNA_VITRINA", "T1": 108},
    "MV60D/I": {"name": "MEDIACOLUMNA VIT 60", "category": "MEDIACOLUMNA_VITRINA", "T1": 117},
    "MV60": {"name": "MEDIACOLUMNA VIT 60 2P", "category": "MEDIACOLUMNA_VITRINA", "T1": 113},
    
    # MEDIACOLUMNA HORNO
    "MH60D/I": {"name": "MEDIACOLUMNA HORNO 60", "category": "MEDIACOLUMNA_HORNO", "T1": 121},
    "MH60": {"name": "MEDIACOLUMNA HORNO 60 2P", "category": "MEDIACOLUMNA_HORNO", "T1": 129},
    
    # MEDIACOLUMNA MICRO
    "MM60D/I": {"name": "MEDIACOLUMNA MICRO 60", "category": "MEDIACOLUMNA_MICRO", "T1": 126},
    "MM60": {"name": "MEDIACOLUMNA MICRO 60 2P", "category": "MEDIACOLUMNA_MICRO", "T1": 130},
    
    # ===========================================
    # ALTILLO
    # ===========================================
    "L30": {"name": "ALTILLO 30", "category": "ALTILLO", "T1": 52},
    "L35": {"name": "ALTILLO 35", "category": "ALTILLO", "T1": 55},
    "L40": {"name": "ALTILLO 40", "category": "ALTILLO", "T1": 59},
    "L45": {"name": "ALTILLO 45", "category": "ALTILLO", "T1": 62},
    "L50": {"name": "ALTILLO 50", "category": "ALTILLO", "T1": 66},
    "L60": {"name": "ALTILLO 60", "category": "ALTILLO", "T1": 71},
    "L70": {"name": "ALTILLO 70", "category": "ALTILLO", "T1": 76},
    "L80": {"name": "ALTILLO 80", "category": "ALTILLO", "T1": 81},
    "L90": {"name": "ALTILLO 90", "category": "ALTILLO", "T1": 87},
    "L100": {"name": "ALTILLO 100", "category": "ALTILLO", "T1": 92},
    
    # ALTILLO VITRINA
    "LV30": {"name": "ALTILLO VITRINA 30", "category": "ALTILLO_VITRINA", "T1": 76},
    "LV35": {"name": "ALTILLO VITRINA 35", "category": "ALTILLO_VITRINA", "T1": 80},
    "LV40": {"name": "ALTILLO VITRINA 40", "category": "ALTILLO_VITRINA", "T1": 81},
    "LV45": {"name": "ALTILLO VITRINA 45", "category": "ALTILLO_VITRINA", "T1": 83},
    "LV50": {"name": "ALTILLO VITRINA 50", "category": "ALTILLO_VITRINA", "T1": 84},
    "LV60": {"name": "ALTILLO VITRINA 60", "category": "ALTILLO_VITRINA", "T1": 87},
    "LV70": {"name": "ALTILLO VITRINA 70", "category": "ALTILLO_VITRINA", "T1": 92},
    "LV80": {"name": "ALTILLO VITRINA 80", "category": "ALTILLO_VITRINA", "T1": 97},
    "LV90": {"name": "ALTILLO VITRINA 90", "category": "ALTILLO_VITRINA", "T1": 102},
    "LV100": {"name": "ALTILLO VITRINA 100", "category": "ALTILLO_VITRINA", "T1": 107},
    
    # ALTILLO DECORATIVO
    "LD30": {"name": "ALTILLO DECORATIVO 30", "category": "ALTILLO_DECORATIVO", "T1": 16},
    "LD35": {"name": "ALTILLO DECORATIVO 35", "category": "ALTILLO_DECORATIVO", "T1": 17},
    "LD40": {"name": "ALTILLO DECORATIVO 40", "category": "ALTILLO_DECORATIVO", "T1": 18},
    "LD45": {"name": "ALTILLO DECORATIVO 45", "category": "ALTILLO_DECORATIVO", "T1": 19},
    "LD50": {"name": "ALTILLO DECORATIVO 50", "category": "ALTILLO_DECORATIVO", "T1": 20},
    "LD60": {"name": "ALTILLO DECORATIVO 60", "category": "ALTILLO_DECORATIVO", "T1": 22},
    "LD70": {"name": "ALTILLO DECORATIVO 70", "category": "ALTILLO_DECORATIVO", "T1": 23},
    "LD80": {"name": "ALTILLO DECORATIVO 80", "category": "ALTILLO_DECORATIVO", "T1": 25},
    "LD90": {"name": "ALTILLO DECORATIVO 90", "category": "ALTILLO_DECORATIVO", "T1": 27},
    "LD100": {"name": "ALTILLO DECORATIVO 100", "category": "ALTILLO_DECORATIVO", "T1": 29},
    
    # ===========================================
    # SOBREENCIMERA
    # ===========================================
    "S30D/I": {"name": "SOBREENCIMERA 30", "category": "SOBREENCIMERA", "T1": 67},
    "S35D/I": {"name": "SOBREENCIMERA 35", "category": "SOBREENCIMERA", "T1": 69},
    "S40D/I": {"name": "SOBREENCIMERA 40", "category": "SOBREENCIMERA", "T1": 71},
    "S45D/I": {"name": "SOBREENCIMERA 45", "category": "SOBREENCIMERA", "T1": 73},
    "S50D/I": {"name": "SOBREENCIMERA 50", "category": "SOBREENCIMERA", "T1": 75},
    "S60D/I": {"name": "SOBREENCIMERA 60", "category": "SOBREENCIMERA", "T1": 78},
    "S60": {"name": "SOBREENCIMERA 60 2P", "category": "SOBREENCIMERA", "T1": 76},
    
    # SOBREENCIMERA CAJON
    "SC30D/I": {"name": "SOBREENCIMERA CAJON 30", "category": "SOBREENCIMERA_CAJON", "T1": 87},
    "SC35D/I": {"name": "SOBREENCIMERA CAJON 35", "category": "SOBREENCIMERA_CAJON", "T1": 90},
    "SC40D/I": {"name": "SOBREENCIMERA CAJON 40", "category": "SOBREENCIMERA_CAJON", "T1": 93},
    "SC45D/I": {"name": "SOBREENCIMERA CAJON 45", "category": "SOBREENCIMERA_CAJON", "T1": 97},
    "SC50D/I": {"name": "SOBREENCIMERA CAJON 50", "category": "SOBREENCIMERA_CAJON", "T1": 100},
    "SC60D/I": {"name": "SOBREENCIMERA CAJON 60", "category": "SOBREENCIMERA_CAJON", "T1": 107},
    "SC60": {"name": "SOBREENCIMERA CAJON 60 2P", "category": "SOBREENCIMERA_CAJON", "T1": 104},
    
    # SOBREENCIMERA VITRINA
    "SV30D/I": {"name": "SOBREENCIMERA VITRINA 30", "category": "SOBREENCIMERA_VITRINA", "T1": 104},
    "SV35D/I": {"name": "SOBREENCIMERA VITRINA 35", "category": "SOBREENCIMERA_VITRINA", "T1": 107},
    "SV40D/I": {"name": "SOBREENCIMERA VITRINA 40", "category": "SOBREENCIMERA_VITRINA", "T1": 111},
    "SV45D/I": {"name": "SOBREENCIMERA VITRINA 45", "category": "SOBREENCIMERA_VITRINA", "T1": 114},
    "SV50D/I": {"name": "SOBREENCIMERA VITRINA 50", "category": "SOBREENCIMERA_VITRINA", "T1": 118},
    "SV60D/I": {"name": "SOBREENCIMERA VITRINA 60", "category": "SOBREENCIMERA_VITRINA", "T1": 125},
    "SV60": {"name": "SOBREENCIMERA VITRINA 60 2P", "category": "SOBREENCIMERA_VITRINA", "T1": 121},
    
    # SOBREENCIMERA VITRINA CAJON
    "SVC30D/I": {"name": "SOBREENCIMERA VIT+CAJ 30", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 121},
    "SVC35D/I": {"name": "SOBREENCIMERA VIT+CAJ 35", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 125},
    "SVC40D/I": {"name": "SOBREENCIMERA VIT+CAJ 40", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 130},
    "SVC45D/I": {"name": "SOBREENCIMERA VIT+CAJ 45", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 134},
    "SVC50D/I": {"name": "SOBREENCIMERA VIT+CAJ 50", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 138},
    "SVC60D/I": {"name": "SOBREENCIMERA VIT+CAJ 60", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 147},
    "SVC60": {"name": "SOBREENCIMERA VIT+CAJ 60 2P", "category": "SOBREENCIMERA_VIT_CAJON", "T1": 143},
}

# Multiplicadores de tarifa (basados en datos extraídos)
# T1 = base, cada tarifa incrementa ~6%
TARIFF_MULTIPLIERS = {
    "T1": 1.00,
    "T2": 1.06,
    "T3": 1.12,
    "T4": 1.18,
    "T5": 1.24,
    "T6": 1.30,
    "T7": 1.36,
    "T8": 1.42,
    "T9": 1.48,
    "T10": 1.54,
    "T11": 1.60,
    "T12": 1.66,
    "T13": 1.72,
    "T14": 1.78,
    "T15": 1.84,
    "T16": 1.90,
    "T17": 1.96,
    "T18": 2.02,
    "T19": 2.08,
    "T20": 2.14,
    "T21": 2.20,
}

print(f"Total productos MV_T1: {len(MV_PRODUCTS_T1)}")
