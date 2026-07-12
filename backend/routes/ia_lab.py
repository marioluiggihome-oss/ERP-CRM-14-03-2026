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
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends

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

# Auth obligatoria: el análisis de planos con IA consume créditos y no debe
# quedar abierto sin token.
try:
    from services.jwt_service import require_auth
    _IALAB_DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover
    _IALAB_DEPS = []

router = APIRouter(prefix="/ia-lab", tags=["IA Lab"], dependencies=_IALAB_DEPS)


# Raíz de categoría del catálogo por tipo detectado por la IA. Se usa con un
# regex "^RAIZ" para cubrir TODAS las variantes: singular y plural y GOLA.
#   MV usa singular: ALTO / BAJO / COLUMNA / SEMICOLUMNA
#   ZC usa plural:   ALTOS / BAJOS / COLUMNAS ... (y "ALTOS GOLA", etc.)
_TIPO_TO_CAT_ROOT = {
    'ALTO': 'ALTO',
    'BAJO': 'BAJO',
    'COLUMNA': 'COLUMNA',
    'SEMICOLUMNA': 'SEMICOLUMNA',
    'COSTADO': 'COSTADO',
}


def _resolve_price(p, library=None):
    """Precio/puntos de un producto. MV y ZC guardan el valor en 'points'; si
    viene a 0, se usa la primera tarifa de zonePoints (T1 para MV, Z1 para ZC)."""
    try:
        price = float(p.get('points', 0) or 0)
    except Exception:
        price = 0
    if not price:
        zp = p.get('zonePoints') or {}
        if isinstance(zp, dict):
            key = 'T1' if (library or '').upper() == 'MV' else 'Z1'
            try:
                price = float(zp.get(key, 0) or 0)
            except Exception:
                price = 0
    return price


async def _get_point_value(library: str = None) -> float:
    """Valor de 1 punto en EUR para la biblioteca (misma fuente que el frontend:
    la colección `libraries`, campo `pointValue`). Se usa para convertir los
    PUNTOS del catálogo a EUR (precio_pvp = puntos × pointValue).

    ASUNCIÓN: el flujo de análisis de plano NO recibe acabado/tarifa, así que los
    PUNTOS provienen de la columna por defecto del producto (`points`, con
    fallback T1/Z1). Aquí solo se convierte esa cifra de puntos a euros; la
    valoración exacta por acabado/tarifa la hace el Presupuestador al volcar.
    Si no se puede resolver el valor de punto, se devuelve 1.0 (puntos == euros).
    """
    try:
        lib = await db.libraries.find_one({"code": (library or 'ZC').upper()}, {"_id": 0})
        pv = float((lib or {}).get('pointValue', 1.0) or 1.0)
        return pv if pv > 0 else 1.0
    except Exception:
        return 1.0


def _to_cm(v):
    """Normaliza una medida a cm. La IA detecta anchos/altos en mm (p.ej. 600)
    y el catálogo los guarda en cm (p.ej. 60); si el valor es 'grande' se asume
    mm y se divide entre 10."""
    try:
        v = float(v or 0)
    except Exception:
        return 0.0
    return v / 10.0 if v >= 200 else v


def _product_width_cm(p) -> float:
    """Ancho REAL del producto en cm.

    CLAVE DEL BUG: los importadores del catálogo (tanto ZC `import_complete_catalog.py`
    como MV `seed_mv_products.py`) guardan `width: 0` en casi todos los muebles; el
    ancho de verdad va CODIFICADO en el código y/o el nombre. Si nos fiábamos del
    campo `width` (=0) TODOS los candidatos empataban en el score y el emparejador
    devolvía siempre el primer mueble de la colección (p.ej. A40D/I), repitiendo el
    mismo SKU y el mismo precio. Aquí extraemos el ancho de forma robusta:

      1. Campo `width` si viene informado (>0).
      2. Código estilo ZC: ancho en mm tras la última P/V (…P600, …V1200).
      3. "600MM" en el nombre.
      4. "40 CM" en el nombre (quitando primero la altura tipo H70/H90).
      5. Código estilo MV: letras iniciales + ancho en cm (A40D/I, BC60, BCGF35, A100).
      6. Primer número de 2-3 cifras del nombre (sin la altura).
    """
    try:
        w = float(p.get('width') or 0)
    except Exception:
        w = 0
    if w > 0:
        return _to_cm(w)

    code = (p.get('code') or '').upper()
    name = (p.get('name') or '').upper()

    # 2. ZC: ancho en mm al final tras P (puerta) o V (vitrina): 9A1P600 → 600mm.
    m = re.search(r'[PV](\d{3,4})$', code)
    if m:
        return int(m.group(1)) / 10.0

    # 3. Milímetros rotulados en el nombre: "…600mm".
    m = re.search(r'(\d{3,4})\s*MM', name)
    if m:
        return int(m.group(1)) / 10.0

    # 4. Centímetros en el nombre. Se quita antes la altura (H70/H90) para no
    #    confundirla con el ancho.
    name_wo_h = re.sub(r'H\s*\d{2,3}', ' ', name)
    m = re.search(r'(\d{2,3})\s*CM', name_wo_h)
    if m:
        return float(m.group(1))

    # 5. MV: letras iniciales + ancho en cm (A40D/I, BC60, BCGF35, ASCE60, A100).
    m = re.search(r'^[A-Z]+(\d{2,3})', code)
    if m:
        val = int(m.group(1))
        if 15 <= val <= 300:
            return float(val)

    # 6. Último recurso: primer número de 2-3 cifras del nombre (sin la altura).
    m = re.search(r'\b(\d{2,3})\b', name_wo_h)
    if m:
        val = int(m.group(1))
        if 15 <= val <= 300:
            return float(val)

    return 0.0


async def _match_by_type_and_width(tipo: str, width: int, height: int, base_filter: dict) -> dict:
    """Empareja por TIPO + ANCHO (y, si ayuda, altura) dentro de la biblioteca.

    Robusto entre ZC y MV: no depende del formato del código, solo de categoría
    (por raíz, cubre singular/plural/GOLA) + medida (normalizada a cm).
    """
    if not tipo or not width:
        return None
    cat_root = _TIPO_TO_CAT_ROOT.get((tipo or '').upper().strip())
    if not cat_root:
        return None

    width_cm = _to_cm(width)
    height_cm = _to_cm(height) if height else 0

    # Candidatos por categoría (regex que cubre ALTO/ALTOS/ALTO GOLA…) + biblioteca.
    cat_filter = {**base_filter, "category": {"$regex": f"^{cat_root}", "$options": "i"}}
    candidates = await db.products.find(cat_filter, {"_id": 0}).to_list(3000)
    if not candidates:
        return None

    def score(p):
        # Ancho REAL del candidato (derivado de código/nombre; el campo width del
        # catálogo suele ser 0 y no sirve para emparejar).
        pw_cm = _product_width_cm(p)
        s = abs(pw_cm - width_cm)
        if height_cm and _to_cm(p.get('height')):
            s += abs(_to_cm(p.get('height')) - height_cm) * 0.3  # la altura pesa menos
        return s

    candidates.sort(key=score)
    best = candidates[0]
    # Aceptar solo si el ancho está razonablemente cerca (±8 cm); los anchos son
    # estándar (30,40,45,60,80,90,120…), así que un buen match debe ser exacto.
    if abs(_product_width_cm(best) - width_cm) > 8:
        return None
    return best


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

    # Valor de punto de la biblioteca (EUR/punto) para convertir puntos → euros.
    point_value = await _get_point_value(library)

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
            # `puntos` = puntos del catálogo; `precio_pvp` = EUR (puntos × valor punto).
            _puntos = _resolve_price(catalog_product, library)
            enriched_item['puntos'] = _puntos
            enriched_item['precio_pvp'] = round(_puntos * point_value, 2)
            enriched_item['categoria'] = catalog_product.get('category', '')
            enriched_item['programa'] = catalog_product.get('programa', 'ESTÁNDAR')
            # El campo width del catálogo suele ser 0 → derivamos el ancho real del
            # código/nombre. Se guarda en mm (como ancho_estimado) para el frontend.
            _cat_w_cm = _product_width_cm(catalog_product)
            enriched_item['ancho_real'] = int(_cat_w_cm * 10) if _cat_w_cm else width
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

RAZONA DE FORMA METÓDICA ANTES DE RESPONDER (piensa paso a paso):
- Recorre el plano de IZQUIERDA a DERECHA y separa lo de ARRIBA (altos) de lo de ABAJO (bajos).
- Cuenta por separado altos, bajos, columnas, semicolumnas y costados; no dupliques ni omitas ninguno.
- Distingue MUEBLE de ELECTRODOMÉSTICO: nevera, horno, microondas, lavavajillas, placa y campana
  NO son muebles del catálogo (márcalos como ELECTRODOMESTICO).
- VERIFICA que cada medida sea REALISTA antes de darla. Rangos válidos:
  · ancho: 300–1200 mm (usa el valor estándar más cercano)
  · alto altos: 35–90 cm · alto bajos: 70–90 cm · columnas: 200–240 cm
  · fondo: ~33 cm en altos, ~58 cm en bajos
  Si una medida se sale de rango (p.ej. fondo de 5 mm), es un ERROR: corrígela al estándar más cercano.
- Prioriza los anchos ROTULADOS en el plano; no inventes medidas. Lee las líneas de
  cota y las cifras escritas junto a cada mueble: esa es la fuente de verdad del ancho.
- LISTA MÓDULO A MÓDULO de IZQUIERDA a DERECHA. Cada entrada de "muebles_detectados"
  es UN módulo físico distinto con SU PROPIO ancho medido en el plano. Los anchos de
  una cocina real son VARIADOS (p.ej. 600, 800, 900): NO repitas el mismo ancho para
  todos los módulos salvo que el plano muestre realmente módulos idénticos.
- NO INVENTES DUPLICADOS: no copies el mismo mueble varias veces. Si dos módulos
  contiguos son realmente iguales (mismo tipo y mismo ancho), inclúyelos como entradas
  separadas SOLO si de verdad existen los dos en el plano; nunca "rellenes" la lista
  repitiendo un módulo.
- Si hay una ISLA o PENÍNSULA, detéctala como una fila de bajos independiente (sus
  propios módulos) y NO la confundas con la fila pegada a la pared.
- Si el plano indica una ESCALA o una medida total de pared, úsala para repartir los
  anchos de los módulos de forma coherente (que la suma de anchos cuadre con el tramo).

COMPLETITUD (CRÍTICO — el error más habitual es DETECTAR DE MENOS):
- Detecta CADA módulo por separado, no solo los evidentes. Una cocina en L o en U
  suele tener MUCHOS muebles (frecuentemente 10–20+). Si has detectado muy pocos,
  REVISA otra vez: casi seguro te has dejado módulos.
- DESCOMPÓN los tramos largos en módulos ESTÁNDAR: una fila continua de bajos de,
  p. ej., 2400 mm NO es un solo mueble; son varios módulos estándar (p. ej.
  600+600+600+600). Cuenta los frentes (puertas/cajones) para deducir cuántos
  módulos hay.
- Incluye SIEMPRE: la fila completa de BAJOS bajo la encimera, la fila completa de
  ALTOS, columnas/torres (horno, microondas, despensa, frigorífico integrado),
  muebles de RINCÓN, costados/laterales vistos, y altillos sobre electrodomésticos.
- Para muebles PARCIALMENTE ocultos o cortados por el borde de la imagen: inclúyelos
  igualmente con tu mejor estimación y "confianza": "BAJA".
- Es MEJOR incluir un módulo dudoso (con confianza BAJA) que OMITIRLO. No descartes
  un mueble solo porque no estés seguro de su medida exacta.
- Antes de responder, comprueba que el nº total de muebles es coherente con el
  TAMAÑO de la cocina visible; si parece bajo, vuelve a recorrer el plano.

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
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Falta la clave del motor de IA (contacta con el administrador)")
        
        # Normalizar biblioteca
        active_library = (library or "ZC").upper()
        logger.info(f"Analyzing kitchen plan for library: {active_library}")
        
        file_content = await file.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        response_text = await analyze_image_with_gemini(
            image_base64=base64_image,
            prompt=build_analysis_prompt(active_library),
            session_id=f"kitchen-plan-{uuid.uuid4().hex[:8]}",
            model="gemini-2.5-pro",
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
            raise HTTPException(status_code=503, detail="Clave del motor de IA rechazada (401). Verifica la clave en la configuración del servidor.")
        elif 'api_key' in ml or 'api key not valid' in ml or '400' in msg:
            raise HTTPException(status_code=503, detail="Error de configuración de IA. Verifica la clave del motor de IA.")
        elif 'not_found' in ml or '404' in msg or 'not found' in ml:
            raise HTTPException(status_code=503, detail="El modelo de IA no está disponible para tu clave. Revisa la configuración del motor de IA.")
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
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Falta la clave del motor de IA (contacta con el administrador)")
        
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
                model="gemini-2.5-pro",
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
