"""
Router para IA Lab - Análisis de planos de cocina con IA
"""
import os
import re
import json
import uuid
import base64
import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

import google.generativeai as genai

from config import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ia-lab", tags=["IA Lab"])


async def search_product_in_catalog(code: str, width: int = None, height: int = None, library: str = None) -> dict:
    """
    Busca un producto en el catálogo por código.
    Intenta varias variantes del código si no encuentra exacto.
    Filtra por biblioteca si se especifica.
    """
    if not code:
        return None

    code = code.upper().strip()

    base_filter = {}
    if library:
        base_filter["library"] = library.upper()

    # 1. Búsqueda exacta
    product = await db.products.find_one({**base_filter, "code": code}, {"_id": 0})
    if product:
        return product

    # 2. Buscar con referencia
    product = await db.products.find_one({**base_filter, "reference": code}, {"_id": 0})
    if product:
        return product

    # 3. Buscar variantes del código
    match = re.match(r'^(\d+)([A-Z]+)(\d*)([A-Z]*)(\d+)$', code)
    if match:
        tipo = match.group(2)
        num_puertas = match.group(3)
        tipo_puerta = match.group(4)
        ancho = match.group(5)

        pattern = f".*{tipo}.*{num_puertas}.*{tipo_puerta}.*{ancho}$"
        product = await db.products.find_one({**base_filter, "code": {"$regex": pattern, "$options": "i"}}, {"_id": 0})
        if product:
            return product

        pattern_simple = f".*{tipo}.*{ancho}$"
        product = await db.products.find_one({**base_filter, "code": {"$regex": pattern_simple, "$options": "i"}}, {"_id": 0})
        if product:
            return product

    # 4. Buscar por dimensiones si se proporcionan
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
    """Enriquece la lista de muebles detectados con información del catálogo."""
    enriched = []

    for item in furniture_list:
        code = item.get('codigo_sugerido', '')
        width = item.get('ancho_estimado', 0)
        height = item.get('alto_estimado', 0) * 10

        catalog_product = await search_product_in_catalog(code, width, height, library)

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
            enriched_item['fondo_real'] = catalog_product.get('depth', item.get('fondo_estimado', 0) * 10)
            enriched_item['product_id'] = catalog_product.get('id', '')
            enriched_item['biblioteca'] = catalog_product.get('library', library or 'ZC')
        else:
            enriched_item['producto_encontrado'] = False
            enriched_item['codigo_catalogo'] = code
            enriched_item['nombre_catalogo'] = f"{item.get('tipo', '')} {item.get('subtipo', '').replace('_', ' ')}"
            enriched_item['puntos'] = 0
            enriched_item['precio_pvp'] = 0
            enriched_item['mensaje'] = f"Producto no encontrado en catálogo {library or 'ZC'} - revisar manualmente"

        enriched.append(enriched_item)

    return enriched


def get_mime_type(content: bytes) -> str:
    """Detecta el tipo MIME de la imagen por sus magic bytes."""
    magic = content[:8]
    if magic[:2] == b'\xff\xd8':
        return "image/jpeg"
    elif magic[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif magic[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    elif magic[8:12] == b'WEBP' if len(content) > 12 else False:
        return "image/webp"
    return "image/jpeg"


async def call_gemini(api_key: str, prompt: str, image_bytes: bytes, system_instruction: str) -> str:
    """Llama a la API de Gemini con una imagen y devuelve el texto de respuesta."""
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_instruction
    )

    mime_type = get_mime_type(image_bytes)
    image_part = {"mime_type": mime_type, "data": image_bytes}

    response = await asyncio.to_thread(
        model.generate_content,
        [prompt, image_part]
    )

    return response.text.strip() if response and response.text else ""


def clean_json_response(response_text: str) -> str:
    """Limpia el JSON de posibles bloques markdown."""
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    return response_text.strip()


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
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

        active_library = (library or "ZC").upper()
        logger.info(f"Analyzing kitchen plan for library: {active_library}")

        file_content = await file.read()

        response_text = await call_gemini(
            api_key=api_key,
            prompt=ANALYSIS_PROMPT_SINGLE,
            image_bytes=file_content,
            system_instruction="Eres un experto en diseño de cocinas. Analiza planos y detecta muebles con precisión."
        )

        response_text = clean_json_response(response_text)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"error": "No se pudo analizar el plano", "raw_response": response_text[:500]}

        # Enriquecer con datos del catálogo
        if 'muebles_detectados' in data:
            data['muebles_detectados'] = await enrich_detected_furniture(data['muebles_detectados'], active_library)

            total_pvp = sum(m.get('precio_pvp', 0) for m in data['muebles_detectados'])
            productos_encontrados = sum(1 for m in data['muebles_detectados'] if m.get('producto_encontrado'))
            productos_no_encontrados = sum(1 for m in data['muebles_detectados'] if not m.get('producto_encontrado'))

            data['resumen_precios'] = {
                'total_pvp': total_pvp,
                'productos_encontrados': productos_encontrados,
                'productos_no_encontrados': productos_no_encontrados,
                'mensaje': f"{productos_encontrados} productos cotizados de {len(data['muebles_detectados'])} detectados",
                'biblioteca': active_library
            }

        logger.info(f"Kitchen plan analyzed: {len(data.get('muebles_detectados', []))} items for {active_library}")
        return {"success": True, "analysis": data, "library": active_library}

    except Exception as e:
        logger.error(f"Kitchen plan analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

        active_library = (library or "ZC").upper()
        logger.info(f"Analyzing {len(files)} kitchen plans for library: {active_library}")

        all_furniture = []
        all_summaries = []

        for idx, file in enumerate(files):
            file_content = await file.read()

            analysis_prompt = f"""Analiza este plano/diseño de cocina (PARED {idx + 1} de {len(files)}) y detecta TODOS los muebles.

IDENTIFICA:
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

            try:
                response_text = await call_gemini(
                    api_key=api_key,
                    prompt=analysis_prompt,
                    image_bytes=file_content,
                    system_instruction="Eres un experto en diseño de cocinas."
                )

                response_text = clean_json_response(response_text)
                data = json.loads(response_text)
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
            except Exception as e:
                logger.warning(f"Could not parse wall {idx + 1}: {e}")

        total_summary = {
            'total_altos': sum(s.get('resumen', {}).get('total_altos', 0) for s in all_summaries),
            'total_bajos': sum(s.get('resumen', {}).get('total_bajos', 0) for s in all_summaries),
            'total_columnas': sum(s.get('resumen', {}).get('total_columnas', 0) for s in all_summaries),
            'total_muebles': len(all_furniture),
            'paredes_analizadas': len(files),
            'biblioteca': active_library
        }

        enriched_furniture = await enrich_detected_furniture(all_furniture, active_library)

        total_pvp = sum(m.get('precio_pvp', 0) for m in enriched_furniture)
        productos_encontrados = sum(1 for m in enriched_furniture if m.get('producto_encontrado'))
        productos_no_encontrados = sum(1 for m in enriched_furniture if not m.get('producto_encontrado'))

        total_summary['resumen_precios'] = {
            'total_pvp': total_pvp,
            'productos_encontrados': productos_encontrados,
            'productos_no_encontrados': productos_no_encontrados,
            'mensaje': f"{productos_encontrados} productos cotizados de {len(enriched_furniture)} detectados"
        }

        logger.info(f"Multi-wall analyzed: {len(enriched_furniture)} items from {len(files)} walls for {active_library}")

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
