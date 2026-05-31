"""
Router para IA Lab - Análisis de planos de cocina con IA
"""
import os
import re
import json
import uuid
import base64
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    LlmChat = None
    UserMessage = None
    ImageContent = None

from config import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ia-lab", tags=["IA Lab"])


# Mapa de tipo detectado por la IA -> categorías del catálogo (ZC y MV).
# El ancho es el dato más fiable de un plano (va rotulado); la altura la
# estima la IA y puede no coincidir, así que el emparejamiento prioriza
# TIPO + ANCHO dentro de la biblioteca correcta.
_TIPO_TO_CATEGORIES = {
    'ALTO': ['ALTOS', 'ALTOS GOLA', 'ALTO GOLA', 'SOBREMODULOS', 'SOBREMÓDULOS', 'VITRINAS'],
    'BAJO': ['BAJOS', 'BAJOS GOLA'],
    'COLUMNA': ['COLUMNAS', 'COLUMNAS GOLA'],
    'SEMICOLUMNA': ['SEMICOLUMNAS', 'SEMICOLUMNAS GOLA'],
    'COSTADO': ['COSTADOS'],
}


async def _match_by_type_and_width(tipo: str, width: int, height: int, base_filter: dict) -> dict:
    """Empareja por TIPO + ANCHO (y, si ayuda, altura) dentro de la biblioteca.

    Estrategia: filtra por las categorías del tipo y busca el producto cuyo
    ancho sea el más cercano al detectado. Es robusto entre librerías (ZC/MV)
    porque no depende del formato del código, solo de categoría + medida.
    """
    if not tipo or not width:
        return None
    cats = _TIPO_TO_CATEGORIES.get((tipo or '').upper())
    if not cats:
        return None

    # Tolerancia de ancho: ±60mm (los anchos son estándar: 300,400,...)
    cat_filter = {
        **base_filter,
        "category": {"$in": cats},
        "width": {"$gte": width - 60, "$lte": width + 60},
    }
    candidates = await db.products.find(cat_filter, {"_id": 0}).to_list(200)
    if not candidates:
        return None

    def score(p):
        pw = float(p.get('width') or 0)
        ph = float(p.get('height') or 0)
        s = abs(pw - width)
        if height:
            s += abs(ph - height) * 0.3  # la altura pesa menos (la estima la IA)
        return s

    candidates.sort(key=score)
    return candidates[0]


async def search_product_in_catalog(code: str, width: int = None, height: int = None,
                                     library: str = None, tipo: str = None) -> dict:
    """
    Busca un producto en el catálogo.
    Orden: código exacto -> referencia -> variantes de código -> TIPO+ANCHO -> dimensiones.
    Filtra por biblioteca si se especifica.
    """
    code = (code or '').upper().strip()

    base_filter = {}
    if library:
        base_filter["library"] = library.upper()

    if code:
        # 1. Búsqueda exacta
        product = await db.products.find_one({**base_filter, "code": code}, {"_id": 0})
        if product:
            return product

        # 2. Buscar con referencia
        product = await db.products.find_one({**base_filter, "reference": code}, {"_id": 0})
        if product:
            return product

        # 3. Buscar variantes del código (formato ZC: 9A1P600, etc.)
        match = re.match(r'^(\d+)([A-Z]+)(\d*)([A-Z]*)(\d+)$', code)
        if match:
            tipo_code = match.group(2)
            num_puertas = match.group(3)
            tipo_puerta = match.group(4)
            ancho = match.group(5)

            pattern = f".*{tipo_code}.*{num_puertas}.*{tipo_puerta}.*{ancho}$"
            product = await db.products.find_one({**base_filter, "code": {"$regex": pattern, "$options": "i"}}, {"_id": 0})
            if product:
                return product

            pattern_simple = f".*{tipo_code}.*{ancho}$"
            product = await db.products.find_one({**base_filter, "code": {"$regex": pattern_simple, "$options": "i"}}, {"_id": 0})
            if product:
                return product

    # 4. Emparejamiento por TIPO + ANCHO (clave para que funcione en MV y ZC
    #    aunque el código sugerido por la IA no exista en esa biblioteca).
    product = await _match_by_type_and_width(tipo, width, height, base_filter)
    if product:
        return product

    # 5. Último recurso: por dimensiones (ancho + alto aproximados).
    if width and height:
        products = await db.products.find({
            **base_filter,
            "width": {"$gte": width - 50, "$lte": width + 50},
            "height": {"$gte": height - 100, "$lte": height + 100}
        }, {"_id": 0}).limit(5).to_list(5)
        if products:
            return products[0]

    return None


async def enrich_detected_furniture(furniture_list: list, library: str = None) -> list:
    """
    Enriquece la lista de muebles detectados con información del catálogo.
    Filtra por biblioteca si se especifica.
    """
    enriched = []

    # Tipos/subtipos que son electrodomésticos o accesorios, NO muebles del catálogo.
    # No deben contar como "producto no encontrado".
    APPLIANCE_TIPOS = {'ELECTRODOMESTICO', 'ELECTRODOMÉSTICO'}
    APPLIANCE_SUBTIPOS = {'CAMPANA', 'EXTRACTOR', 'PLACA', 'PLACA_COCCION', 'HORNO',
                          'MICROONDAS', 'NEVERA', 'FRIGORIFICO', 'LAVAVAJILLAS',
                          'FREGADERO', 'GRIFO', 'VITRO', 'INDUCCION'}

    def _is_appliance(it):
        tipo = (it.get('tipo') or '').upper()
        subtipo = (it.get('subtipo') or '').upper()
        nombre = (it.get('nombre') or it.get('descripcion') or '').upper()
        if tipo in APPLIANCE_TIPOS:
            return True
        if any(s in subtipo for s in APPLIANCE_SUBTIPOS):
            return True
        if any(s in nombre for s in APPLIANCE_SUBTIPOS):
            return True
        return False

    for item in furniture_list:
        code = item.get('codigo_sugerido', '')

        # Normalización defensiva de unidades.
        # El prompt pide ancho_estimado en mm y alto/fondo en cm, pero la IA
        # ocasionalmente devuelve todo en la misma unidad. Detectamos por rango:
        #   - Anchos válidos en mm: 250-1500. Si llega < 200, era cm → *10.
        #   - Altos válidos en cm: 30-260. Si llega > 500, era mm → /10.
        raw_ancho = item.get('ancho_estimado', 0) or 0
        raw_alto = item.get('alto_estimado', 0) or 0
        raw_fondo = item.get('fondo_estimado', 0) or 0

        width = int(raw_ancho * 10) if raw_ancho and raw_ancho < 200 else int(raw_ancho)
        alto_cm = int(raw_alto / 10) if raw_alto and raw_alto > 500 else int(raw_alto)
        height = alto_cm * 10  # cm → mm para búsqueda en catálogo
        fondo_cm = int(raw_fondo / 10) if raw_fondo and raw_fondo > 200 else int(raw_fondo)

        catalog_product = await search_product_in_catalog(
            code, width, height, library, tipo=item.get('tipo')
        )
        
        enriched_item = {**item}
        
        if catalog_product:
            enriched_item['producto_encontrado'] = True
            enriched_item['codigo_catalogo'] = catalog_product.get('code', code)
            enriched_item['nombre_catalogo'] = catalog_product.get('name', '')
            enriched_item['puntos'] = catalog_product.get('points', 0) or catalog_product.get('T1', 0)
            enriched_item['precio_pvp'] = catalog_product.get('points', 0) or catalog_product.get('T1', 0)
            enriched_item['categoria'] = catalog_product.get('category', '')
            enriched_item['programa'] = catalog_product.get('programa', 'ESTÁNDAR')
            enriched_item['ancho_real'] = catalog_product.get('width', width)
            enriched_item['alto_real'] = catalog_product.get('height', height)
            enriched_item['fondo_real'] = catalog_product.get('depth', fondo_cm * 10)
            enriched_item['product_id'] = catalog_product.get('id', '')
            enriched_item['biblioteca'] = catalog_product.get('library', library or 'ZC')
        elif _is_appliance(item):
            # Electrodoméstico/accesorio: no es un mueble del catálogo. No cuenta como
            # "no encontrado" ni "encontrado"; se marca aparte para la sección propia.
            enriched_item['producto_encontrado'] = False
            enriched_item['es_electrodomestico'] = True
            enriched_item['codigo_catalogo'] = code
            enriched_item['nombre_catalogo'] = f"{item.get('tipo', '')} {item.get('subtipo', '').replace('_', ' ')}".strip()
            enriched_item['puntos'] = 0
            enriched_item['precio_pvp'] = 0
            enriched_item['mensaje'] = "Electrodoméstico / accesorio (no es mueble del catálogo)"
        else:
            enriched_item['producto_encontrado'] = False
            enriched_item['es_electrodomestico'] = False
            enriched_item['codigo_catalogo'] = code
            enriched_item['nombre_catalogo'] = f"{item.get('tipo', '')} {item.get('subtipo', '').replace('_', ' ')}"
            enriched_item['puntos'] = 0
            enriched_item['precio_pvp'] = 0
            enriched_item['mensaje'] = f"Producto no encontrado en catálogo {library or 'ZC'} - revisar manualmente"

        enriched.append(enriched_item)
    
    return enriched


ANALYSIS_PROMPT_SINGLE = """Analiza este plano/diseño de cocina y detecta TODOS los muebles y elementos visibles.

IDENTIFICA CON CUIDADO:
1. Muebles ALTOS (armarios de pared superiores) - Incluye altillos sobre electrodomésticos
2. Muebles BAJOS (armarios de base con encimera)
3. COLUMNAS (muebles de altura completa - despensas, hornos)
4. SEMICOLUMNAS (muebles de media altura)
5. COSTADOS (paneles laterales decorativos - junto a electrodomésticos, al final de muebles)
6. ALTILLOS COMBI (muebles pequeños sobre frigoríficos o similar)
7. Electrodomésticos integrados (horno, microondas, nevera, lavavajillas)

SISTEMA DE CÓDIGOS (MUY IMPORTANTE):
- ALTOS 35-60cm altura: {altura}A{nPuertas}P{anchoMM} → Ej: 60A1P600 = Alto 60cm 1 Puerta 600mm
- ALTOS 70-90cm altura: {altura/10}A{nPuertas}P{anchoMM} → Ej: 9A1P600 = Alto 90cm 1 Puerta 600mm
- BAJOS: {altura/10}B{nPuertas}P{anchoMM} → Ej: 7B1P600 = Bajo 70cm 1 Puerta 600mm
- COLUMNAS: {altura/10}CD{nPuertas}P{anchoMM} → Ej: 22CD1P600 = Columna 220cm 1 Puerta 600mm
- SEMICOLUMNAS: {altura/10}SM{nPuertas}P{anchoMM} → Ej: 11SM1P450 = Semicolumna 110cm 1 Puerta 450mm
- VITRINAS: usar V en lugar de P → Ej: 9A1V600 = Alto 90cm 1 Vitrina 600mm

ANCHOS ESTÁNDAR: 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200mm
ALTURAS ALTOS: 35, 40, 45, 60, 70, 80, 90cm
ALTURAS BAJOS: 70, 80cm
ALTURAS COLUMNAS: 200, 220, 240cm

Para cada mueble detectado proporciona:
- tipo: ALTO/BAJO/COLUMNA/SEMICOLUMNA/COSTADO/ELECTRODOMESTICO
- subtipo: 1_PUERTA, 2_PUERTAS, CAJON, VITRINA, HORNO, FREGADERO, etc.
- ancho_estimado: ancho en mm (usar valores estándar)
- alto_estimado: altura en cm
- fondo_estimado: fondo en cm (33 para altos estándar, 58 para bajos)
- posicion: ubicación en el plano
- codigo_sugerido: USAR EL SISTEMA DE CÓDIGOS DESCRITO ARRIBA
- confianza: ALTA/MEDIA/BAJA

Responde SOLO con JSON válido:
{
  "muebles_detectados": [
    {
      "tipo": "ALTO",
      "subtipo": "1_PUERTA",
      "ancho_estimado": 600,
      "alto_estimado": 90,
      "fondo_estimado": 33,
      "posicion": "sobre fregadero",
      "codigo_sugerido": "9A1P600",
      "confianza": "ALTA"
    }
  ],
  "resumen": {
    "total_altos": 0,
    "total_bajos": 0,
    "total_columnas": 0,
    "total_semicolumnas": 0,
    "total_costados": 0,
    "total_altillos": 0,
    "metros_lineales_estimados": 0
  },
  "observaciones": "Notas adicionales"
}"""


# Límite máximo: 10MB
MAX_KITCHEN_IMAGE = 10 * 1024 * 1024
MAX_KITCHEN_BASE64 = MAX_KITCHEN_IMAGE * 4 // 3


def build_analysis_prompt(library: str) -> str:
    """Devuelve el prompt de análisis adaptado a la biblioteca.

    El sistema de códigos del prompt base es ZC. Para MV (Muebles Valencia) la
    nomenclatura es distinta, así que NO se le pide a la IA que invente códigos
    ZC: el emparejamiento real lo hace el backend por TIPO + ANCHO contra el
    catálogo de la biblioteca. Lo importante en ambas es detectar bien el
    TIPO y el ANCHO (que va rotulado en el plano).
    """
    lib = (library or 'ZC').upper()
    if lib == 'MV':
        return ANALYSIS_PROMPT_SINGLE + """

IMPORTANTE — BIBLIOTECA MV (MUEBLES VALENCIA):
- Esta cocina usa el catálogo MV, cuya nomenclatura de códigos es DISTINTA a la
  descrita arriba. NO fuerces el formato de código ZC.
- Lo CRÍTICO es detectar correctamente para cada mueble: el TIPO
  (ALTO/BAJO/COLUMNA/SEMICOLUMNA/COSTADO), el ANCHO en mm (suele ir rotulado
  en el plano: 300, 400, 450, 500, 600, 700, 800, 900, 1000, 1200) y el nº de
  puertas. La altura/fondo estímalas como siempre.
- En "codigo_sugerido" pon tu mejor estimación, pero prioriza acertar TIPO y
  ANCHO: el sistema buscará el producto MV que corresponda por tipo y medida.
"""
    return ANALYSIS_PROMPT_SINGLE


@router.post("/analyze-kitchen-plan")
async def analyze_kitchen_plan(
    file: UploadFile = File(...),
    library: Optional[str] = Form(default="ZC")
):
    """
    Analiza un plano de cocina usando Gemini Vision y detecta los muebles.
    Filtra productos por la biblioteca especificada (ZC o MV).
    """
    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Añade GEMINI_API_KEY en variables de entorno")
        
        # Normalizar biblioteca
        active_library = (library or "ZC").upper()
        logger.info(f"Analyzing kitchen plan for library: {active_library}")
        
        file_content = await file.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        response_text = await analyze_image_with_gemini(
            image_base64=base64_image,
            prompt=build_analysis_prompt(active_library),
            session_id=f"kitchen-plan-{uuid.uuid4().hex[:8]}",
            model="gemini-2.0-flash",
        )
        
        # Clean JSON from markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"error": "No se pudo analizar el plano", "raw_response": response_text[:500]}
        
        # Enrich with catalog data - FILTRANDO POR BIBLIOTECA
        if 'muebles_detectados' in data:
            data['muebles_detectados'] = await enrich_detected_furniture(data['muebles_detectados'], active_library)
            
            total_pvp = sum(m.get('precio_pvp', 0) for m in data['muebles_detectados'])
            productos_encontrados = sum(1 for m in data['muebles_detectados'] if m.get('producto_encontrado'))
            electrodomesticos = sum(1 for m in data['muebles_detectados'] if m.get('es_electrodomestico'))
            # "No encontrados" reales = ni encontrados ni electrodomésticos
            productos_no_encontrados = sum(1 for m in data['muebles_detectados']
                                           if not m.get('producto_encontrado') and not m.get('es_electrodomestico'))
            muebles_cotizables = len(data['muebles_detectados']) - electrodomesticos

            data['resumen_precios'] = {
                'total_pvp': total_pvp,
                'total_puntos': sum(m.get('puntos', 0) for m in data['muebles_detectados']),
                'productos_encontrados': productos_encontrados,
                'productos_no_encontrados': productos_no_encontrados,
                'electrodomesticos': electrodomesticos,
                'mensaje': f"{productos_encontrados} productos cotizados de {muebles_cotizables} muebles detectados",
                'biblioteca': active_library
            }
        
        logger.info(f"Kitchen plan analyzed: {len(data.get('muebles_detectados', []))} furniture items detected for {active_library}")
        return {"success": True, "analysis": data, "library": active_library}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Kitchen plan analysis error: {e}\n{tb}")
        # Dar mensaje más descriptivo al usuario
        msg = str(e)
        ml = msg.lower()
        if 'quota' in ml or '429' in msg:
            raise HTTPException(status_code=429, detail="Límite de uso de IA alcanzado. Espera un momento.")
        elif '401' in msg or 'unauthenticated' in ml or 'access_token_type_unsupported' in ml or 'invalid authentication' in ml:
            raise HTTPException(status_code=503, detail="GEMINI_API_KEY rechazada por Google (401). Verifica que sea una API key válida de AI Studio (empieza por 'AIza'), sin espacios ni comillas, y que la Generative Language API esté activada.")
        elif 'api_key' in ml or 'api key not valid' in ml or '400' in msg:
            raise HTTPException(status_code=503, detail="Error de configuración de IA. Verifica GEMINI_API_KEY.")
        elif 'not_found' in ml or '404' in msg or 'not found' in ml:
            raise HTTPException(status_code=503, detail="El modelo de IA no está disponible para tu clave. Actualiza el SDK o revisa el acceso a Gemini en tu proyecto.")
        elif 'timeout' in msg.lower():
            raise HTTPException(status_code=504, detail="La IA tardó demasiado. Intenta con una imagen más pequeña.")
        else:
            raise HTTPException(status_code=500, detail=f"Error al analizar: {msg[:200]}")


@router.post("/analyze-kitchen-plan-multi")
async def analyze_kitchen_plan_multi(
    files: List[UploadFile] = File(...),
    library: Optional[str] = Form(default="ZC")
):
    """
    Analiza MÚLTIPLES planos de cocina (varias paredes).
    Filtra productos por la biblioteca especificada (ZC o MV).
    """
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            api_key = None  # Permite usar Gemini directo si está disponible
        
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Añade GEMINI_API_KEY en variables de entorno")
        
        # Normalizar biblioteca
        active_library = (library or "ZC").upper()
        logger.info(f"Analyzing multiple kitchen plans for library: {active_library}")
        
        all_furniture = []
        all_summaries = []
        
        for idx, file in enumerate(files):
            file_content = await file.read()
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            analysis_prompt = f"""Analiza este plano/diseño de cocina (PARED {idx + 1} de {len(files)}) y detecta TODOS los muebles.

IDENTIFICA CON CUIDADO:
1. Muebles ALTOS (armarios de pared superiores)
2. Muebles BAJOS (armarios de base con encimera)
3. COLUMNAS (muebles de altura completa)
4. SEMICOLUMNAS (muebles de media altura)
5. COSTADOS (paneles laterales decorativos)
6. Electrodomésticos integrados

SISTEMA DE CÓDIGOS:
- ALTOS: {{altura}}A{{nPuertas}}P{{anchoMM}} → Ej: 60A1P600, 9A2P800
- BAJOS: {{altura/10}}B{{nPuertas}}P{{anchoMM}} → Ej: 7B1P600, 7B2P800
- COLUMNAS: {{altura/10}}CD{{nPuertas}}P{{anchoMM}} → Ej: 22CD1P600
- SEMICOLUMNAS: {{altura/10}}SM{{nPuertas}}P{{anchoMM}}
- VITRINAS: usar V en lugar de P → Ej: 9A1V600

ANCHOS ESTÁNDAR: 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200mm

Responde SOLO con JSON:
{{
  "pared": {idx + 1},
  "muebles_detectados": [
    {{
      "tipo": "ALTO/BAJO/COLUMNA/SEMICOLUMNA/COSTADO/ELECTRODOMESTICO",
      "subtipo": "1_PUERTA/2_PUERTAS/CAJON/VITRINA/HORNO/FREGADERO",
      "ancho_estimado": 600,
      "alto_estimado": 90,
      "fondo_estimado": 33,
      "posicion": "descripción",
      "codigo_sugerido": "9A1P600",
      "confianza": "ALTA/MEDIA/BAJA"
    }}
  ],
  "resumen": {{
    "total_altos": 0,
    "total_bajos": 0,
    "total_columnas": 0
  }}
}}"""

            # Para MV la nomenclatura de códigos es distinta: no forzar el formato
            # ZC; el backend empareja por TIPO + ANCHO contra el catálogo MV.
            if active_library == 'MV':
                analysis_prompt += """

IMPORTANTE — BIBLIOTECA MV (MUEBLES VALENCIA): el sistema de códigos de arriba es
de otra biblioteca. NO fuerces ese formato. Prioriza detectar bien el TIPO y el
ANCHO (rotulado en el plano); el sistema buscará el producto MV correspondiente.
"""

            response_text = await analyze_image_with_gemini(
                image_base64=base64_image,
                prompt=analysis_prompt,
                session_id=f"kitchen-multi-{uuid.uuid4().hex[:8]}",
                model="gemini-2.0-flash",
            )
            
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            try:
                data = json.loads(response_text.strip())
                furniture = data.get('muebles_detectados', [])
                for item in furniture:
                    item['pared'] = idx + 1
                    item['archivo'] = file.filename
                all_furniture.extend(furniture)
                all_summaries.append({
                    'pared': idx + 1,
                    'archivo': file.filename,
                    'muebles': len(furniture),
                    'resumen': data.get('resumen', {})
                })
            except json.JSONDecodeError:
                logger.warning(f"Could not parse JSON for wall {idx + 1}")
        
        total_summary = {
            'total_altos': sum(s.get('resumen', {}).get('total_altos', 0) for s in all_summaries),
            'total_bajos': sum(s.get('resumen', {}).get('total_bajos', 0) for s in all_summaries),
            'total_columnas': sum(s.get('resumen', {}).get('total_columnas', 0) for s in all_summaries),
            'total_muebles': len(all_furniture),
            'paredes_analizadas': len(files),
            'biblioteca': active_library
        }
        
        # Enriquecer con datos del catálogo - FILTRANDO POR BIBLIOTECA
        enriched_furniture = await enrich_detected_furniture(all_furniture, active_library)
        
        total_pvp = sum(m.get('precio_pvp', 0) for m in enriched_furniture)
        productos_encontrados = sum(1 for m in enriched_furniture if m.get('producto_encontrado'))
        electrodomesticos = sum(1 for m in enriched_furniture if m.get('es_electrodomestico'))
        productos_no_encontrados = sum(1 for m in enriched_furniture
                                       if not m.get('producto_encontrado') and not m.get('es_electrodomestico'))
        muebles_cotizables = len(enriched_furniture) - electrodomesticos

        total_summary['resumen_precios'] = {
            'total_pvp': total_pvp,
            'total_puntos': sum(m.get('puntos', 0) for m in enriched_furniture),
            'productos_encontrados': productos_encontrados,
            'productos_no_encontrados': productos_no_encontrados,
            'electrodomesticos': electrodomesticos,
            'mensaje': f"{productos_encontrados} productos cotizados de {muebles_cotizables} muebles detectados"
        }
        
        logger.info(f"Multi-wall kitchen plan analyzed: {len(enriched_furniture)} furniture items from {len(files)} walls for {active_library}")
        
        return {
            "success": True,
            "library": active_library,
            "analysis": {
                "muebles_detectados": enriched_furniture,
                "resumen": total_summary,
                "paredes": all_summaries
            }
        }
        
    except Exception as e:
        logger.error(f"Multi-wall kitchen plan analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
