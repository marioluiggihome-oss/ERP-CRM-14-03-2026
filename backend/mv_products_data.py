# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Datos de la Tarifa MV extraídos de las imágenes JPG
Productos organizados por código con precios por tarifa
"""

# Datos extraídos de análisis de imágenes
# Formato: {codigo: {nombre, categoria, tariffPrices: {T1: precio, T2: precio, ...}}}

MV_PRODUCTS = {
    # ============================================
    # BAJO (Base cabinets)
    # ============================================
    "B25D/I": {"name": "BAJO 25", "category": "BAJO", "tariffPrices": {"T1": 41}},
    "B30D/I": {"name": "BAJO 30", "category": "BAJO", "tariffPrices": {"T1": 42}},
    "B35D/I": {"name": "BAJO 35", "category": "BAJO", "tariffPrices": {"T1": 43}},
    "B40D/I": {"name": "BAJO 40", "category": "BAJO", "tariffPrices": {"T1": 44}},
    "B45D/I": {"name": "BAJO 45", "category": "BAJO", "tariffPrices": {"T1": 45}},
    "B50D/I": {"name": "BAJO 50", "category": "BAJO", "tariffPrices": {"T1": 46}},
    "B60D/I": {"name": "BAJO 60", "category": "BAJO", "tariffPrices": {"T1": 60}},
    "B60": {"name": "BAJO 60", "category": "BAJO", "tariffPrices": {"T1": 56}},
    "B70": {"name": "BAJO 70", "category": "BAJO", "tariffPrices": {"T1": 59}},
    "B80": {"name": "BAJO 80", "category": "BAJO", "tariffPrices": {"T1": 63}},
    "B90": {"name": "BAJO 90", "category": "BAJO", "tariffPrices": {"T1": 67}},
    "B100": {"name": "BAJO 100", "category": "BAJO", "tariffPrices": {"T1": 71}},
    
    # BAJO FREGADERO
    "BF45D/I": {"name": "BAJO FREGADERO 45", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 40}},
    "BF50D/I": {"name": "BAJO FREGADERO 50", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 41}},
    "BF60D/I": {"name": "BAJO FREGADERO 60", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 42}},
    "BF60": {"name": "BAJO FREGADERO 60", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 43}},
    "BF70": {"name": "BAJO FREGADERO 70", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 44}},
    "BF80": {"name": "BAJO FREGADERO 80", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 45}},
    "BF90": {"name": "BAJO FREGADERO 90", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 46}},
    "BF100": {"name": "BAJO FREGADERO 100", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 52}},
    "BF120": {"name": "BAJO FREGADERO 120", "category": "BAJO_FREGADERO", "tariffPrices": {"T1": 50}},
    
    # BAJO TERMINAL
    "BT30D/I": {"name": "BAJO TERMINAL 30", "category": "BAJO_TERMINAL", "tariffPrices": {"T1": 58}},
    "BTZ30D/I": {"name": "BAJO TERMINAL ZOCALO 30", "category": "BAJO_TERMINAL", "tariffPrices": {"T1": 60}},
    "BTP33D/I": {"name": "BAJO TERMINAL PUERTA 33", "category": "BAJO_TERMINAL", "tariffPrices": {"T1": 63}},
    
    # BAJO HORNO
    "BH60": {"name": "BAJO HORNO 60", "category": "BAJO_HORNO", "tariffPrices": {"T1": 37}},
    "BHC60": {"name": "BAJO HORNO CAJON 60", "category": "BAJO_HORNO", "tariffPrices": {"T1": 45}},
    "BHZ60": {"name": "BAJO HORNO ZOCALO 60", "category": "BAJO_HORNO", "tariffPrices": {"T1": 77}},
    "BHG60": {"name": "BAJO HORNO GAVETA 60", "category": "BAJO_HORNO", "tariffPrices": {"T1": 80}},
    
    # BAJO RINCON
    "BR90D/I": {"name": "BAJO RINCON 90", "category": "BAJO_RINCON", "tariffPrices": {"T1": 87}},
    "BR95D/I": {"name": "BAJO RINCON 95", "category": "BAJO_RINCON", "tariffPrices": {"T1": 88}},
    "BR100D/I": {"name": "BAJO RINCON 100", "category": "BAJO_RINCON", "tariffPrices": {"T1": 63}},
    "BR105D/I": {"name": "BAJO RINCON 105", "category": "BAJO_RINCON", "tariffPrices": {"T1": 64}},
    "BRI95D/I": {"name": "BAJO RINCON INDEP 95", "category": "BAJO_RINCON", "tariffPrices": {"T1": 162}},
    "BRU95D/I": {"name": "BAJO RINCON UNIDO 95", "category": "BAJO_RINCON", "tariffPrices": {"T1": 158}},
    
    # BAJO PUERTA Y CAJON
    "BPC30D/I": {"name": "BAJO PUERTA CAJON 30", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 168}},
    "BPC35D/I": {"name": "BAJO PUERTA CAJON 35", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 171}},
    "BPC40D/I": {"name": "BAJO PUERTA CAJON 40", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 173}},
    "BPC45D/I": {"name": "BAJO PUERTA CAJON 45", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 176}},
    "BPC50D/I": {"name": "BAJO PUERTA CAJON 50", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 179}},
    "BPC60D/I": {"name": "BAJO PUERTA CAJON 60", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 184}},
    "BPC60": {"name": "BAJO PUERTA CAJON 60", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 150}},
    "BPC80": {"name": "BAJO PUERTA CAJON 80", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 160}},
    "BPC100": {"name": "BAJO PUERTA CAJON 100", "category": "BAJO_PUERTA_CAJON", "tariffPrices": {"T1": 170}},
    
    # BAJO CAJONES
    "BC30": {"name": "BAJO 3 CAJONES 30", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 112}},
    "BC35": {"name": "BAJO 3 CAJONES 35", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 114}},
    "BC40": {"name": "BAJO 3 CAJONES 40", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 116}},
    "BC45": {"name": "BAJO 3 CAJONES 45", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 118}},
    "BC50": {"name": "BAJO 3 CAJONES 50", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 120}},
    "BC60": {"name": "BAJO 3 CAJONES 60", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 124}},
    "BC70": {"name": "BAJO 3 CAJONES 70", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 126}},
    "BC80": {"name": "BAJO 3 CAJONES 80", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 130}},
    "BC90": {"name": "BAJO 3 CAJONES 90", "category": "BAJO_CAJONES", "tariffPrices": {"T1": 134}},
    
    # BAJO CAJONES GAVETA
    "BCG30": {"name": "BAJO CAJONES GAVETA 30", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 140}},
    "BCG35": {"name": "BAJO CAJONES GAVETA 35", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 142}},
    "BCG40": {"name": "BAJO CAJONES GAVETA 40", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 144}},
    "BCG45": {"name": "BAJO CAJONES GAVETA 45", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 147}},
    "BCG50": {"name": "BAJO CAJONES GAVETA 50", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 150}},
    "BCG60": {"name": "BAJO CAJONES GAVETA 60", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 146}},
    "BCG70": {"name": "BAJO CAJONES GAVETA 70", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 155}},
    "BCG80": {"name": "BAJO CAJONES GAVETA 80", "category": "BAJO_CAJONES_GAVETA", "tariffPrices": {"T1": 162}},
    
    # BAJO GAVETAS FRENTE
    "BGF60": {"name": "BAJO GAVETAS FRENTE 60", "category": "BAJO_GAVETAS", "tariffPrices": {"T1": 97}},
    "BGF70": {"name": "BAJO GAVETAS FRENTE 70", "category": "BAJO_GAVETAS", "tariffPrices": {"T1": 123}},
    "BGF80": {"name": "BAJO GAVETAS FRENTE 80", "category": "BAJO_GAVETAS", "tariffPrices": {"T1": 129}},
    "BGF90": {"name": "BAJO GAVETAS FRENTE 90", "category": "BAJO_GAVETAS", "tariffPrices": {"T1": 134}},
    
    # ============================================
    # ALTO (Wall cabinets)
    # ============================================
    "A25D/I": {"name": "ALTO 25", "category": "ALTO", "tariffPrices": {"T1": 55}},
    "A30D/I": {"name": "ALTO 30", "category": "ALTO", "tariffPrices": {"T1": 56}},
    "A35D/I": {"name": "ALTO 35", "category": "ALTO", "tariffPrices": {"T1": 58}},
    "A40D/I": {"name": "ALTO 40", "category": "ALTO", "tariffPrices": {"T1": 61}},
    "A45D/I": {"name": "ALTO 45", "category": "ALTO", "tariffPrices": {"T1": 63}},
    "A50D/I": {"name": "ALTO 50", "category": "ALTO", "tariffPrices": {"T1": 67}},
    "A60D/I": {"name": "ALTO 60", "category": "ALTO", "tariffPrices": {"T1": 72}},
    "A60": {"name": "ALTO 60", "category": "ALTO", "tariffPrices": {"T1": 70}},
    "A70": {"name": "ALTO 70", "category": "ALTO", "tariffPrices": {"T1": 75}},
    "A80": {"name": "ALTO 80", "category": "ALTO", "tariffPrices": {"T1": 80}},
    "A90": {"name": "ALTO 90", "category": "ALTO", "tariffPrices": {"T1": 85}},
    "A100": {"name": "ALTO 100", "category": "ALTO", "tariffPrices": {"T1": 90}},
    
    # ALTO VITRINA
    "AV30D/I": {"name": "ALTO VITRINA 30", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 70}},
    "AV35D/I": {"name": "ALTO VITRINA 35", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 68}},
    "AV40D/I": {"name": "ALTO VITRINA 40", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 75}},
    "AV45D/I": {"name": "ALTO VITRINA 45", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 76}},
    "AV50D/I": {"name": "ALTO VITRINA 50", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 73}},
    "AV60D/I": {"name": "ALTO VITRINA 60", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 78}},
    "AV60": {"name": "ALTO VITRINA 60", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 84}},
    "AV70": {"name": "ALTO VITRINA 70", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 75}},
    "AV80": {"name": "ALTO VITRINA 80", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 71}},
    "AV90": {"name": "ALTO VITRINA 90", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 70}},
    "AV100": {"name": "ALTO VITRINA 100", "category": "ALTO_VITRINA", "tariffPrices": {"T1": 68}},
    
    # ALTO DECORATIVO
    "AD40": {"name": "ALTO DECORATIVO 40", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 38}},
    "AD45": {"name": "ALTO DECORATIVO 45", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 37}},
    "AD50": {"name": "ALTO DECORATIVO 50", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 36}},
    "AD60": {"name": "ALTO DECORATIVO 60", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 42}},
    "AD70": {"name": "ALTO DECORATIVO 70", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 39}},
    "AD80": {"name": "ALTO DECORATIVO 80", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 41}},
    "AD90": {"name": "ALTO DECORATIVO 90", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 44}},
    "AD100": {"name": "ALTO DECORATIVO 100", "category": "ALTO_DECORATIVO", "tariffPrices": {"T1": 48}},
    
    # ALTO CAMPANA
    "ASCE60D/I": {"name": "ALTO CAMPANA EXTRAPLANA 60", "category": "ALTO_CAMPANA", "tariffPrices": {"T1": 70}},
    "ASCE60": {"name": "ALTO CAMPANA EXTRAPLANA 60", "category": "ALTO_CAMPANA", "tariffPrices": {"T1": 54}},
    "ASCE90": {"name": "ALTO CAMPANA EXTRAPLANA 90", "category": "ALTO_CAMPANA", "tariffPrices": {"T1": 43}},
    "ASC60D/I": {"name": "ALTO CAMPANA CLASICA 60", "category": "ALTO_CAMPANA", "tariffPrices": {"T1": 36}},
    "ASC60": {"name": "ALTO CAMPANA CLASICA 60", "category": "ALTO_CAMPANA", "tariffPrices": {"T1": 38}},
    
    # ALTO ESCURREPLATOS
    "AE45D/I": {"name": "ALTO ESCURREPLATOS 45", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 100}},
    "AE50D/I": {"name": "ALTO ESCURREPLATOS 50", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 107}},
    "AE60D/I": {"name": "ALTO ESCURREPLATOS 60", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 121}},
    "AE60": {"name": "ALTO ESCURREPLATOS 60", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 138}},
    "AE70": {"name": "ALTO ESCURREPLATOS 70", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 149}},
    "AE80": {"name": "ALTO ESCURREPLATOS 80", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 160}},
    "AE90": {"name": "ALTO ESCURREPLATOS 90", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 172}},
    "AE100": {"name": "ALTO ESCURREPLATOS 100", "category": "ALTO_ESCURREPLATOS", "tariffPrices": {"T1": 185}},
    
    # ALTO MICROONDAS
    "AM60D/I": {"name": "ALTO MICROONDAS 60", "category": "ALTO_MICROONDAS", "tariffPrices": {"T1": 76}},
    "AM60": {"name": "ALTO MICROONDAS 60", "category": "ALTO_MICROONDAS", "tariffPrices": {"T1": 109}},
    "AMF60D/I": {"name": "ALTO MICROONDAS FONDO 60", "category": "ALTO_MICROONDAS", "tariffPrices": {"T1": 90}},
    "AMF60": {"name": "ALTO MICROONDAS FONDO 60", "category": "ALTO_MICROONDAS", "tariffPrices": {"T1": 115}},
    
    # ALTO CALENTADOR
    "ACA45D/I": {"name": "ALTO CALENTADOR 45", "category": "ALTO_CALENTADOR", "tariffPrices": {"T1": 87}},
    "ACA50D/I": {"name": "ALTO CALENTADOR 50", "category": "ALTO_CALENTADOR", "tariffPrices": {"T1": 93}},
    "ACA60D/I": {"name": "ALTO CALENTADOR 60", "category": "ALTO_CALENTADOR", "tariffPrices": {"T1": 105}},
    "ACA60": {"name": "ALTO CALENTADOR 60", "category": "ALTO_CALENTADOR", "tariffPrices": {"T1": 121}},
    
    # ALTO CALDERA
    "ACC60D/I": {"name": "ALTO CALDERA 60", "category": "ALTO_CALDERA", "tariffPrices": {"T1": 106}},
    "ACC60": {"name": "ALTO CALDERA 60", "category": "ALTO_CALDERA", "tariffPrices": {"T1": 130}},
    
    # ALTO SOBREFRIGO
    "ASF60D/I": {"name": "ALTO SOBREFRIGO 60", "category": "ALTO_SOBREFRIGO", "tariffPrices": {"T1": 60}},
    "ASF60": {"name": "ALTO SOBREFRIGO 60", "category": "ALTO_SOBREFRIGO", "tariffPrices": {"T1": 70}},
    
    # ALTO TERMINAL
    "AT30D/I": {"name": "ALTO TERMINAL 30", "category": "ALTO_TERMINAL", "tariffPrices": {"T1": 52}},
    "ATP33D/I": {"name": "ALTO TERMINAL PUERTA 33", "category": "ALTO_TERMINAL", "tariffPrices": {"T1": 59}},
    
    # ALTO RINCON
    "AR60D/I": {"name": "ALTO RINCON 60", "category": "ALTO_RINCON", "tariffPrices": {"T1": 135}},
    "AR65D/I": {"name": "ALTO RINCON 65", "category": "ALTO_RINCON", "tariffPrices": {"T1": 141}},
    "ARI65D/I": {"name": "ALTO RINCON INDEP 65", "category": "ALTO_RINCON", "tariffPrices": {"T1": 157}},
    "ARU65D/I": {"name": "ALTO RINCON UNIDO 65", "category": "ALTO_RINCON", "tariffPrices": {"T1": 162}},
    "ARC63D/I": {"name": "ALTO RINCON CHAFLAN 63", "category": "ALTO_RINCON", "tariffPrices": {"T1": 84}},
    
    # ALTO ABATIBLE
    "AA45": {"name": "ALTO ABATIBLE 45", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 147}},
    "AA50": {"name": "ALTO ABATIBLE 50", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 152}},
    "AA60": {"name": "ALTO ABATIBLE 60", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 182}},
    "AA70": {"name": "ALTO ABATIBLE 70", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 193}},
    "AA80": {"name": "ALTO ABATIBLE 80", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 232}},
    "AA90": {"name": "ALTO ABATIBLE 90", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 255}},
    "AA100": {"name": "ALTO ABATIBLE 100", "category": "ALTO_ABATIBLE", "tariffPrices": {"T1": 278}},
    
    # ALTO COMBINADO
    "AC45": {"name": "ALTO COMBINADO 45", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 150}},
    "AC50": {"name": "ALTO COMBINADO 50", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 156}},
    "AC60": {"name": "ALTO COMBINADO 60", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 188}},
    "AC70": {"name": "ALTO COMBINADO 70", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 198}},
    "AC80": {"name": "ALTO COMBINADO 80", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 238}},
    "AC90": {"name": "ALTO COMBINADO 90", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 261}},
    "AC100": {"name": "ALTO COMBINADO 100", "category": "ALTO_COMBINADO", "tariffPrices": {"T1": 284}},
    
    # ALTO COMBINADO PLUS
    "ACP45": {"name": "ALTO COMBINADO PLUS 45", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 143}},
    "ACP50": {"name": "ALTO COMBINADO PLUS 50", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 152}},
    "ACP60": {"name": "ALTO COMBINADO PLUS 60", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 163}},
    "ACP70": {"name": "ALTO COMBINADO PLUS 70", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 174}},
    "ACP80": {"name": "ALTO COMBINADO PLUS 80", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 205}},
    "ACP90": {"name": "ALTO COMBINADO PLUS 90", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 226}},
    "ACP100": {"name": "ALTO COMBINADO PLUS 100", "category": "ALTO_COMBINADO_PLUS", "tariffPrices": {"T1": 247}},
    
    # ALTO COMBINADO PLUS J
    "ACPJ45": {"name": "ALTO COMBINADO PLUS J 45", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 140}},
    "ACPJ50": {"name": "ALTO COMBINADO PLUS J 50", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 134}},
    "ACPJ60": {"name": "ALTO COMBINADO PLUS J 60", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 143}},
    "ACPJ70": {"name": "ALTO COMBINADO PLUS J 70", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 146}},
    "ACPJ80": {"name": "ALTO COMBINADO PLUS J 80", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 177}},
    "ACPJ90": {"name": "ALTO COMBINADO PLUS J 90", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 196}},
    "ACPJ100": {"name": "ALTO COMBINADO PLUS J 100", "category": "ALTO_COMBINADO_PLUS_J", "tariffPrices": {"T1": 215}},
    
    # ============================================
    # ALTILLO (Small overhead)
    # ============================================
    "L30": {"name": "ALTILLO 30", "category": "ALTILLO", "tariffPrices": {"T1": 60}},
    "L35": {"name": "ALTILLO 35", "category": "ALTILLO", "tariffPrices": {"T1": 64}},
    "L40": {"name": "ALTILLO 40", "category": "ALTILLO", "tariffPrices": {"T1": 68}},
    "L45": {"name": "ALTILLO 45", "category": "ALTILLO", "tariffPrices": {"T1": 72}},
    "L50": {"name": "ALTILLO 50", "category": "ALTILLO", "tariffPrices": {"T1": 76}},
    "L60": {"name": "ALTILLO 60", "category": "ALTILLO", "tariffPrices": {"T1": 82}},
    "L70": {"name": "ALTILLO 70", "category": "ALTILLO", "tariffPrices": {"T1": 88}},
    "L80": {"name": "ALTILLO 80", "category": "ALTILLO", "tariffPrices": {"T1": 94}},
    "L90": {"name": "ALTILLO 90", "category": "ALTILLO", "tariffPrices": {"T1": 100}},
    "L100": {"name": "ALTILLO 100", "category": "ALTILLO", "tariffPrices": {"T1": 106}},
    
    # ALTILLO VITRINA
    "LV30": {"name": "ALTILLO VITRINA 30", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 88}},
    "LV35": {"name": "ALTILLO VITRINA 35", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 92}},
    "LV40": {"name": "ALTILLO VITRINA 40", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 94}},
    "LV45": {"name": "ALTILLO VITRINA 45", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 96}},
    "LV50": {"name": "ALTILLO VITRINA 50", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 97}},
    "LV60": {"name": "ALTILLO VITRINA 60", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 100}},
    "LV70": {"name": "ALTILLO VITRINA 70", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 106}},
    "LV80": {"name": "ALTILLO VITRINA 80", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 112}},
    "LV90": {"name": "ALTILLO VITRINA 90", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 118}},
    "LV100": {"name": "ALTILLO VITRINA 100", "category": "ALTILLO_VITRINA", "tariffPrices": {"T1": 124}},
    
    # ALTILLO DECORATIVO
    "LD30": {"name": "ALTILLO DECORATIVO 30", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 19}},
    "LD35": {"name": "ALTILLO DECORATIVO 35", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 20}},
    "LD40": {"name": "ALTILLO DECORATIVO 40", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 21}},
    "LD45": {"name": "ALTILLO DECORATIVO 45", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 22}},
    "LD50": {"name": "ALTILLO DECORATIVO 50", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 23}},
    "LD60": {"name": "ALTILLO DECORATIVO 60", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 25}},
    "LD70": {"name": "ALTILLO DECORATIVO 70", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 27}},
    "LD80": {"name": "ALTILLO DECORATIVO 80", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 29}},
    "LD90": {"name": "ALTILLO DECORATIVO 90", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 31}},
    "LD100": {"name": "ALTILLO DECORATIVO 100", "category": "ALTILLO_DECORATIVO", "tariffPrices": {"T1": 33}},
    
    # ============================================
    # SOBREENCIMERA (Countertop units)
    # ============================================
    "S30D/I": {"name": "SOBREENCIMERA 30", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 78}},
    "S35D/I": {"name": "SOBREENCIMERA 35", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 80}},
    "S40D/I": {"name": "SOBREENCIMERA 40", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 82}},
    "S45D/I": {"name": "SOBREENCIMERA 45", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 84}},
    "S50D/I": {"name": "SOBREENCIMERA 50", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 86}},
    "S60D/I": {"name": "SOBREENCIMERA 60", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 90}},
    "S60": {"name": "SOBREENCIMERA 60", "category": "SOBREENCIMERA", "tariffPrices": {"T1": 88}},
    
    # SOBREENCIMERA CAJON
    "SC30D/I": {"name": "SOBREENCIMERA CAJON 30", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 100}},
    "SC35D/I": {"name": "SOBREENCIMERA CAJON 35", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 104}},
    "SC40D/I": {"name": "SOBREENCIMERA CAJON 40", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 108}},
    "SC45D/I": {"name": "SOBREENCIMERA CAJON 45", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 112}},
    "SC50D/I": {"name": "SOBREENCIMERA CAJON 50", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 116}},
    "SC60D/I": {"name": "SOBREENCIMERA CAJON 60", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 124}},
    "SC60": {"name": "SOBREENCIMERA CAJON 60", "category": "SOBREENCIMERA_CAJON", "tariffPrices": {"T1": 120}},
    
    # SOBREENCIMERA VITRINA
    "SV30D/I": {"name": "SOBREENCIMERA VITRINA 30", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 120}},
    "SV35D/I": {"name": "SOBREENCIMERA VITRINA 35", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 124}},
    "SV40D/I": {"name": "SOBREENCIMERA VITRINA 40", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 128}},
    "SV45D/I": {"name": "SOBREENCIMERA VITRINA 45", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 132}},
    "SV50D/I": {"name": "SOBREENCIMERA VITRINA 50", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 136}},
    "SV60D/I": {"name": "SOBREENCIMERA VITRINA 60", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 144}},
    "SV60": {"name": "SOBREENCIMERA VITRINA 60", "category": "SOBREENCIMERA_VITRINA", "tariffPrices": {"T1": 140}},
    
    # SOBREENCIMERA VITRINA CAJON
    "SVC30D/I": {"name": "SOBREENCIMERA VIT CAJON 30", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 140}},
    "SVC35D/I": {"name": "SOBREENCIMERA VIT CAJON 35", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 145}},
    "SVC40D/I": {"name": "SOBREENCIMERA VIT CAJON 40", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 150}},
    "SVC45D/I": {"name": "SOBREENCIMERA VIT CAJON 45", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 155}},
    "SVC50D/I": {"name": "SOBREENCIMERA VIT CAJON 50", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 160}},
    "SVC60D/I": {"name": "SOBREENCIMERA VIT CAJON 60", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 170}},
    "SVC60": {"name": "SOBREENCIMERA VIT CAJON 60", "category": "SOBREENCIMERA_VIT_CAJON", "tariffPrices": {"T1": 165}},
    
    # ============================================
    # COLUMNA (Tall units)
    # ============================================
    "CD30D/I": {"name": "COLUMNA DESPENSERO 30", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 134}},
    "CD35D/I": {"name": "COLUMNA DESPENSERO 35", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 141}},
    "CD40D/I": {"name": "COLUMNA DESPENSERO 40", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 148}},
    "CD45D/I": {"name": "COLUMNA DESPENSERO 45", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 155}},
    "CD50D/I": {"name": "COLUMNA DESPENSERO 50", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 162}},
    "CD60D/I": {"name": "COLUMNA DESPENSERO 60", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 176}},
    "CD60": {"name": "COLUMNA DESPENSERO 60", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 172}},
    "CD70": {"name": "COLUMNA DESPENSERO 70", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 188}},
    "CD80": {"name": "COLUMNA DESPENSERO 80", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 204}},
    "CD90": {"name": "COLUMNA DESPENSERO 90", "category": "COLUMNA_DESPENSERO", "tariffPrices": {"T1": 220}},
    
    # COLUMNA ESCOBERO
    "CE60D/I": {"name": "COLUMNA ESCOBERO 60", "category": "COLUMNA_ESCOBERO", "tariffPrices": {"T1": 105}},
    "CE60": {"name": "COLUMNA ESCOBERO 60", "category": "COLUMNA_ESCOBERO", "tariffPrices": {"T1": 120}},
    
    # COLUMNA FRIGO
    "CF60D/I": {"name": "COLUMNA FRIGO 60", "category": "COLUMNA_FRIGO", "tariffPrices": {"T1": 185}},
    "CF60": {"name": "COLUMNA FRIGO 60", "category": "COLUMNA_FRIGO", "tariffPrices": {"T1": 200}},
    "CF60A": {"name": "COLUMNA FRIGO ABATIBLE 60", "category": "COLUMNA_FRIGO", "tariffPrices": {"T1": 210}},
    "CF60F": {"name": "COLUMNA FRIGO FREE 60", "category": "COLUMNA_FRIGO", "tariffPrices": {"T1": 220}},
    
    # COLUMNA HORNO
    "CH60D/I": {"name": "COLUMNA HORNO 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 160}},
    "CH60": {"name": "COLUMNA HORNO 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 266}},
    "CHPC60D/I": {"name": "COLUMNA HORNO PUERTA CAJON 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 276}},
    "CHPC60": {"name": "COLUMNA HORNO PUERTA CAJON 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 311}},
    "CHGC60D/I": {"name": "COLUMNA HORNO GAVETA CAJON 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 290}},
    "CHGC60": {"name": "COLUMNA HORNO GAVETA CAJON 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 325}},
    "CHC60D/I": {"name": "COLUMNA HORNO CAJONES 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 310}},
    "CHC60": {"name": "COLUMNA HORNO CAJONES 60", "category": "COLUMNA_HORNO", "tariffPrices": {"T1": 345}},
    
    # COLUMNA HORNO MICRO
    "CHM60D/I": {"name": "COLUMNA HORNO MICRO 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 245}},
    "CHM60": {"name": "COLUMNA HORNO MICRO 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 280}},
    "CHMG60D/I": {"name": "COLUMNA HORNO MICRO GAVETA 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 260}},
    "CHMG60": {"name": "COLUMNA HORNO MICRO GAVETA 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 295}},
    "CHMC60D/I": {"name": "COLUMNA HORNO MICRO CAJONES 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 285}},
    "CHMC60": {"name": "COLUMNA HORNO MICRO CAJONES 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 320}},
    "CHMCG60D/I": {"name": "COLUMNA HORNO MICRO CAJ GAV 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 300}},
    "CHMCG60": {"name": "COLUMNA HORNO MICRO CAJ GAV 60", "category": "COLUMNA_HORNO_MICRO", "tariffPrices": {"T1": 335}},
    
    # ============================================
    # MEDIACOLUMNA (Mid-height units)
    # ============================================
    "M30D/I": {"name": "MEDIACOLUMNA 30", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 80}},
    "M35D/I": {"name": "MEDIACOLUMNA 35", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 85}},
    "M40D/I": {"name": "MEDIACOLUMNA 40", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 90}},
    "M45D/I": {"name": "MEDIACOLUMNA 45", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 95}},
    "M50D/I": {"name": "MEDIACOLUMNA 50", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 100}},
    "M60D/I": {"name": "MEDIACOLUMNA 60", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 110}},
    "M60": {"name": "MEDIACOLUMNA 60", "category": "MEDIACOLUMNA", "tariffPrices": {"T1": 105}},
    
    # MEDIACOLUMNA VITRINA
    "MV30D/I": {"name": "MEDIACOLUMNA VITRINA 30", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 105}},
    "MV35D/I": {"name": "MEDIACOLUMNA VITRINA 35", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 110}},
    "MV40D/I": {"name": "MEDIACOLUMNA VITRINA 40", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 115}},
    "MV45D/I": {"name": "MEDIACOLUMNA VITRINA 45", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 120}},
    "MV50D/I": {"name": "MEDIACOLUMNA VITRINA 50", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 125}},
    "MV60D/I": {"name": "MEDIACOLUMNA VITRINA 60", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 135}},
    "MV60": {"name": "MEDIACOLUMNA VITRINA 60", "category": "MEDIACOLUMNA_VITRINA", "tariffPrices": {"T1": 130}},
    
    # MEDIACOLUMNA PUERTA GAVETA
    "MPG30D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 30", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 184}},
    "MPG35D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 35", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 194}},
    "MPG40D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 40", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 210}},
    "MPG45D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 45", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 221}},
    "MPG50D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 50", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 233}},
    "MPG60D/I": {"name": "MEDIACOLUMNA PUERTA GAVETA 60", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 254}},
    "MPG60": {"name": "MEDIACOLUMNA PUERTA GAVETA 60", "category": "MEDIACOLUMNA_PUERTA_GAVETA", "tariffPrices": {"T1": 140}},
    
    # MEDIACOLUMNA VITRINA GAVETA
    "MVG30D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 30", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 200}},
    "MVG35D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 35", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 210}},
    "MVG40D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 40", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 220}},
    "MVG45D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 45", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 230}},
    "MVG50D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 50", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 240}},
    "MVG60D/I": {"name": "MEDIACOLUMNA VITRINA GAVETA 60", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 260}},
    "MVG60": {"name": "MEDIACOLUMNA VITRINA GAVETA 60", "category": "MEDIACOLUMNA_VIT_GAVETA", "tariffPrices": {"T1": 145}},
    
    # MEDIACOLUMNA HORNO
    "MPH60D/I": {"name": "MEDIACOLUMNA HORNO 60", "category": "MEDIACOLUMNA_HORNO", "tariffPrices": {"T1": 140}},
    "MPH60": {"name": "MEDIACOLUMNA HORNO 60", "category": "MEDIACOLUMNA_HORNO", "tariffPrices": {"T1": 149}},
    
    # MEDIACOLUMNA MICROONDAS
    "MPM60D/I": {"name": "MEDIACOLUMNA MICRO 60", "category": "MEDIACOLUMNA_MICRO", "tariffPrices": {"T1": 145}},
    "MPM60": {"name": "MEDIACOLUMNA MICRO 60", "category": "MEDIACOLUMNA_MICRO", "tariffPrices": {"T1": 150}},
    
    # ============================================
    # PUERTAS (Doors)
    # ============================================
    "P25": {"name": "PUERTA 25", "category": "PUERTA", "tariffPrices": {"T1": 10}},
    "P30": {"name": "PUERTA 30", "category": "PUERTA", "tariffPrices": {"T1": 11}},
    "P35": {"name": "PUERTA 35", "category": "PUERTA", "tariffPrices": {"T1": 12}},
    "P40": {"name": "PUERTA 40", "category": "PUERTA", "tariffPrices": {"T1": 13}},
    "P45": {"name": "PUERTA 45", "category": "PUERTA", "tariffPrices": {"T1": 14}},
    "P50": {"name": "PUERTA 50", "category": "PUERTA", "tariffPrices": {"T1": 15}},
    "P60": {"name": "PUERTA 60", "category": "PUERTA", "tariffPrices": {"T1": 17}},
    
    # PUERTA VITRINA
    "PV30": {"name": "PUERTA VITRINA 30", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 20}},
    "PV35": {"name": "PUERTA VITRINA 35", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 22}},
    "PV40": {"name": "PUERTA VITRINA 40", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 24}},
    "PV45": {"name": "PUERTA VITRINA 45", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 26}},
    "PV50": {"name": "PUERTA VITRINA 50", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 28}},
    "PV60": {"name": "PUERTA VITRINA 60", "category": "PUERTA_VITRINA", "tariffPrices": {"T1": 32}},
    
    # PUERTA VITRINA INGLESA
    "PVI30": {"name": "PUERTA VITRINA INGLESA 30", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 41}},
    "PVI35": {"name": "PUERTA VITRINA INGLESA 35", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 45}},
    "PVI40": {"name": "PUERTA VITRINA INGLESA 40", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 49}},
    "PVI45": {"name": "PUERTA VITRINA INGLESA 45", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 53}},
    "PVI50": {"name": "PUERTA VITRINA INGLESA 50", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 57}},
    "PVI60": {"name": "PUERTA VITRINA INGLESA 60", "category": "PUERTA_VIT_INGLESA", "tariffPrices": {"T1": 65}},
    
    # PUERTA REJILLA
    "PR30": {"name": "PUERTA REJILLA 30", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 41}},
    "PR35": {"name": "PUERTA REJILLA 35", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 45}},
    "PR40": {"name": "PUERTA REJILLA 40", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 48}},
    "PR45": {"name": "PUERTA REJILLA 45", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 51}},
    "PR50": {"name": "PUERTA REJILLA 50", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 56}},
    "PR60": {"name": "PUERTA REJILLA 60", "category": "PUERTA_REJILLA", "tariffPrices": {"T1": 63}},
    
    # ============================================
    # BOTELLERO (Bottle rack)
    # ============================================
    "BOA": {"name": "BOTELLERO ALTO", "category": "BOTELLERO", "tariffPrices": {"T1": 200}},
    "BOS": {"name": "BOTELLERO SOBREENCIMERA", "category": "BOTELLERO", "tariffPrices": {"T1": 85}},
    "BOC": {"name": "BOTELLERO COLUMNA", "category": "BOTELLERO", "tariffPrices": {"T1": 250}},
}

# Número total de productos
TOTAL_PRODUCTS = len(MV_PRODUCTS)
print(f"Total productos MV definidos: {TOTAL_PRODUCTS}")
