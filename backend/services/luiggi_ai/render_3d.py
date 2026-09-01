# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LuiggiAI Engine - Servicio de Render 3D
========================================
Genera renders fotorrealistas de cocinas y espacios interiores
a partir de descripciones en texto natural o voz transcrita.

Integra el skill de kitchen-3d-render para construir prompts
optimizados que producen resultados de alta calidad.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from enum import Enum

from .config import get_ai_config
from .engine_core import get_engine

logger = logging.getLogger("luiggi_ai.render_3d")


class RoomType(str, Enum):
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    OFFICE = "office"
    CUSTOM = "custom"


class RenderStyle(str, Enum):
    PHOTOREALISTIC = "photorealistic"
    ARCHITECTURAL = "architectural"
    MAGAZINE = "magazine"
    MINIMALIST = "minimalist"
    WARM = "warm"
    INDUSTRIAL = "industrial"


class KitchenLayout(str, Enum):
    L_SHAPE = "L-shape"
    U_SHAPE = "U-shape"
    GALLEY = "galley"
    ISLAND = "island"
    STRAIGHT = "straight"
    PENINSULA = "peninsula"


# ─── Catálogo de materiales para prompts ──────────────────────────────────────

COUNTERTOP_MATERIALS = {
    "marble_white": "Carrara white marble with subtle grey veining",
    "marble_black": "Nero Marquina black marble with white veining",
    "granite_black": "absolute black polished granite",
    "quartz_white": "engineered white quartz with minimal veining",
    "quartz_calacatta": "Calacatta quartz with bold grey and gold veining",
    "wood_walnut": "solid walnut wood butcher block",
    "wood_oak": "natural light oak wood countertop",
    "concrete": "polished concrete with smooth matte finish",
    "dekton": "ultra-compact Dekton surface in neutral tone",
    "stainless_steel": "brushed stainless steel professional surface",
}

CABINET_MATERIALS = {
    "oak_natural": "natural light oak wood with visible grain",
    "oak_dark": "dark stained oak wood",
    "walnut": "rich walnut wood with warm brown tones",
    "white_matte": "matte white lacquered flat-panel",
    "white_gloss": "high-gloss white lacquered",
    "grey_matte": "matte grey lacquered flat-panel",
    "anthracite": "dark anthracite grey matte finish",
    "sage_green": "sage green painted shaker-style",
    "navy_blue": "deep navy blue painted",
    "black_matte": "matte black flat-panel modern",
    "cream": "warm cream colored traditional style",
    "olive": "olive green contemporary flat-panel",
}

HANDLE_STYLES = {
    "none": "handleless push-to-open system",
    "integrated": "integrated J-pull channel handles",
    "bar_black": "slim matte black bar handles",
    "bar_brass": "brushed brass bar handles",
    "bar_chrome": "polished chrome bar handles",
    "knob_black": "round matte black knobs",
    "knob_brass": "round brushed brass knobs",
    "cup_black": "matte black cup pulls",
    "leather": "leather loop handles in tan",
}

FLOOR_MATERIALS = {
    "wood_oak": "wide-plank natural oak hardwood flooring",
    "wood_walnut": "dark walnut herringbone parquet",
    "tile_white": "large format white porcelain tiles",
    "tile_grey": "large format grey porcelain tiles",
    "tile_terracotta": "terracotta clay tiles with warm patina",
    "marble_white": "white marble floor tiles with grey veining",
    "concrete": "polished concrete floor",
    "tile_hexagon": "hexagonal cement tiles with geometric pattern",
}

LIGHTING_STYLES = {
    "pendant_modern": "modern minimalist pendant lights over island",
    "pendant_industrial": "industrial black metal pendant lights",
    "recessed": "recessed LED ceiling spotlights",
    "under_cabinet": "warm LED under-cabinet strip lighting",
    "chandelier": "contemporary chandelier as focal point",
    "track": "adjustable track lighting system",
    "natural": "abundant natural light from large windows",
}


# Principios de diseño profesional de cocina que el "cerebro" del render debe
# respetar (en inglés, para el modelo de imagen). Se inyectan cuando la pieza es
# una cocina, para que el resultado tenga criterio de diseñador, no solo estética.
PRO_KITCHEN_DESIGN_PRINCIPLES = (
    "Apply professional kitchen design principles: (1) Work triangle — keep "
    "sink, hob/cooktop and fridge in a logical, efficient triangle, not crammed "
    "together nor too far apart. (2) Ergonomic heights — worktop ~90 cm, wall "
    "units ~55-60 cm above the worktop, extractor hood ~65-75 cm above the hob, "
    "tall/oven columns with the oven at a comfortable height. (3) Lighting in "
    "layers — natural daylight, ambient ceiling light and warm under-cabinet task "
    "lighting over the worktop. (4) Balanced composition and proportions — "
    "symmetry where it helps, consistent reveal gaps, aligned horizontal lines "
    "(worktop, wall-unit bottoms, handles). (5) Material coherence — at most 2-3 "
    "main materials/finishes that harmonize, with the worktop and backsplash "
    "relating to the cabinet fronts. (6) Realistic detailing — plinth/toe-kick, "
    "continuous worktop with matching upstand, integrated and aligned appliances, "
    "visible but tasteful hardware. The space must look designed by a professional "
    "kitchen designer: functional, ergonomic, well-lit and visually balanced."
)


# Prefijo de prompt para IA 3 (Gemini premium / fallback de Flux)
_PREMIUM_PROMPT_PREFIX = (
    "ULTRA-PREMIUM PHOTOREALISTIC KITCHEN RENDER. "
    "Professional architectural photography, shot with Phase One IQ4 150MP medium format camera, "
    "Schneider Kreuznach 28mm LS lens, f/8, ISO 100, perfect exposure. "
    "Physically-based rendering (PBR) with path tracing, subsurface scattering on stone surfaces, "
    "anisotropic reflections on metal, micro-detail wood grain texture at 16K resolution. "
    "Cinematic natural daylight from floor-to-ceiling windows, soft fill light, "
    "warm accent LED under-cabinet strips. Perfect depth of field, tack-sharp foreground, "
    "subtle bokeh on background. Hyper-realistic material response: fingerprint-free matte lacquer, "
    "veined marble with translucency, brushed metal with directional grain. "
    "Award-winning interior design magazine quality. No CGI artifacts, no plastic look."
)


def _etiqueta_de_motor(modelo: str) -> str:
    """El nombre de casa de un modelo de imagen.

    Qué modelo hay detrás no se le enseña a nadie que no sea master (secreto
    industrial, y está en las condiciones de uso). Pero para comparar dos
    renders hace falta saber si son del mismo motor o no, así que sube una
    etiqueta y no el identificador.
    """
    m = (modelo or "").lower()
    if "3-pro-image" in m:
        return "Pro"
    if "flash-image" in m:
        return "Estándar"
    if "flux" in m:
        return "Flux"
    return "otro"


class Render3DService:
    """Servicio de generación de renders 3D fotorrealistas."""

    def __init__(self):
        self.config = get_ai_config()
        self.engine = get_engine()

    def build_kitchen_prompt(
        self,
        layout: str = "L-shape",
        countertop: str = "quartz_white",
        cabinets: str = "white_matte",
        handles: str = "bar_black",
        floor: str = "wood_oak",
        lighting: str = "natural",
        style: str = "photorealistic",
        additional_details: Optional[str] = None,
        appliances: Optional[List[str]] = None,
        colors_accent: Optional[str] = None,
    ) -> str:
        """
        Construye un prompt optimizado para render 3D de cocina.
        """
        # Resolver materiales
        countertop_desc = COUNTERTOP_MATERIALS.get(countertop, countertop)
        cabinet_desc = CABINET_MATERIALS.get(cabinets, cabinets)
        handle_desc = HANDLE_STYLES.get(handles, handles)
        floor_desc = FLOOR_MATERIALS.get(floor, floor)
        lighting_desc = LIGHTING_STYLES.get(lighting, lighting)

        # Estilo de renderizado (con realismo reforzado)
        style_instructions = {
            "photorealistic": "Ultra-photorealistic architectural interior photograph, indistinguishable from a real photo, shot on a full-frame DSLR with a 24-35mm lens, physically-based rendering (PBR), realistic global illumination and soft natural daylight from windows, accurate soft shadows, subtle reflections and ambient occlusion, true-to-life material micro-detail (wood grain, brushed metal, matte/satin finishes), neutral white balance, high dynamic range, fine 8K detail, shallow depth of field",
            "architectural": "Professional architectural visualization, clean lines, accurate proportions, realistic neutral daylight, PBR materials, soft realistic shadows",
            "magazine": "Interior design magazine photograph quality, professionally styled, warm inviting natural light, photorealistic PBR materials, editorial composition",
            "minimalist": "Clean minimalist photorealistic interior, uncluttered surfaces, soft natural shadows, realistic matte materials",
            "warm": "Warm cozy photorealistic interior, golden-hour natural lighting, lived-in feeling, realistic textures and soft shadows",
            "industrial": "Industrial loft photorealistic interior, exposed materials with realistic texture, dramatic but natural contrast lighting",
        }
        style_desc = style_instructions.get(style, style_instructions["photorealistic"])

        # Construir prompt
        prompt_parts = [
            f"{style_desc}.",
            f"A modern {layout} kitchen design.",
            f"Countertops: {countertop_desc}.",
            f"Cabinets: {cabinet_desc}.",
            f"Hardware: {handle_desc}.",
            f"Flooring: {floor_desc}.",
            f"Lighting: {lighting_desc}.",
        ]

        if appliances:
            appliances_text = ", ".join(appliances)
            prompt_parts.append(f"Appliances: {appliances_text}.")

        if colors_accent:
            prompt_parts.append(f"Accent colors: {colors_accent}.")

        if additional_details:
            prompt_parts.append(f"Additional details: {additional_details}.")

        # Instrucciones técnicas finales
        prompt_parts.extend([
            # Escala y proporciones reales de cocina (anclaje físico)
            "Real-world kitchen proportions: base cabinets ~90 cm high with a recessed "
            "toe-kick plinth at the floor, wall cabinets mounted with a ~55-60 cm gap above "
            "the worktop, a continuous worktop of consistent thickness with a matching "
            "upstand/backsplash, and seamless integrated appliances flush with the cabinet "
            "fronts. Keep all module widths, heights and gaps to realistic cabinetry scale.",
            # Cámara y óptica
            "Camera: eye-level (~150 cm) interior photograph on a full-frame DSLR with a "
            "24-35 mm lens, two-point perspective from a front corner, vertical lines kept "
            "perfectly straight (no fisheye distortion), showing the full kitchen layout.",
            # Materiales y luz fotorrealistas
            "Realism: physically-based (PBR) materials with accurate roughness, micro-detail "
            "and reflectivity — visible wood grain, true stone/quartz veining that wraps the "
            "worktop edge, satin or matte lacquer with subtle sheen, brushed metal hardware. "
            "Realistic global illumination, soft directional daylight from a window, accurate "
            "contact shadows, ambient occlusion and subtle reflections on glossy surfaces. "
            "Neutral white balance, natural color grading, high dynamic range. It must look "
            "like a REAL professional interior photograph.",
            # Coherencia geométrica
            "Consistency: keep cabinet doors, drawers and handles straight, equal in size, "
            "evenly spaced and perfectly aligned; reveal gaps between fronts uniform; do not "
            "duplicate, merge, warp, bend or omit cabinet modules; walls, floor joints, "
            "worktop edges and ceiling lines must stay straight and in correct perspective.",
            # Composición
            "Composition: wide-angle shot in 16:9 landscape orientation, framing the full "
            "kitchen run from a corner so all cabinetry is visible, well-balanced and uncluttered.",
            # Prompt negativo explícito (lo que NO debe aparecer)
            "Negative — strictly avoid: cartoon / CGI / videogame / 3D-render look, plastic or "
            "waxy surfaces, flat or ambient-only lighting, oversaturated or neon colors, blurry "
            "or low-detail textures, warped or melted geometry, crooked or misaligned doors, "
            "floating cabinets, duplicated or merged modules, extra invented appliances or "
            "decoration, people, hands, text, watermarks, logos and reflections of a camera.",
            PRO_KITCHEN_DESIGN_PRINCIPLES,
        ])

        return " ".join(prompt_parts)

    def parse_natural_language(self, description: str) -> Dict[str, Any]:
        """
        Parsea una descripción en lenguaje natural para extraer parámetros de render.
        Útil para entrada por voz o texto libre.

        Args:
            description: Texto libre describiendo la cocina deseada

        Returns:
            Dict con parámetros extraídos para build_kitchen_prompt
        """
        desc_lower = description.lower()
        params = {}

        # Detectar layout
        if any(x in desc_lower for x in ["en l", "l-shape", "forma de l"]):
            params["layout"] = "L-shape"
        elif any(x in desc_lower for x in ["en u", "u-shape", "forma de u"]):
            params["layout"] = "U-shape"
        elif any(x in desc_lower for x in ["isla", "island"]):
            params["layout"] = "island"
        elif any(x in desc_lower for x in ["lineal", "recta", "straight"]):
            params["layout"] = "straight"
        elif any(x in desc_lower for x in ["galley", "pasillo"]):
            params["layout"] = "galley"
        elif any(x in desc_lower for x in ["peninsula", "pen\u00ednsula"]):
            params["layout"] = "peninsula"

        # Detectar encimera
        if any(x in desc_lower for x in ["m\u00e1rmol blanco", "marmol blanco", "carrara"]):
            params["countertop"] = "marble_white"
        elif any(x in desc_lower for x in ["m\u00e1rmol negro", "marmol negro", "nero"]):
            params["countertop"] = "marble_black"
        elif any(x in desc_lower for x in ["granito"]):
            params["countertop"] = "granite_black"
        elif any(x in desc_lower for x in ["cuarzo", "quartz", "silestone"]):
            params["countertop"] = "quartz_white"
        elif any(x in desc_lower for x in ["madera nogal", "walnut"]):
            params["countertop"] = "wood_walnut"
        elif any(x in desc_lower for x in ["madera roble", "oak"]):
            params["countertop"] = "wood_oak"
        elif any(x in desc_lower for x in ["hormig\u00f3n", "cemento", "concrete"]):
            params["countertop"] = "concrete"

        # Detectar muebles/gabinetes
        if any(x in desc_lower for x in ["roble natural", "roble claro"]):
            params["cabinets"] = "oak_natural"
        elif any(x in desc_lower for x in ["roble oscuro"]):
            params["cabinets"] = "oak_dark"
        elif any(x in desc_lower for x in ["nogal"]):
            params["cabinets"] = "walnut"
        elif any(x in desc_lower for x in ["blanco mate"]):
            params["cabinets"] = "white_matte"
        elif any(x in desc_lower for x in ["blanco brillo", "blanco brillante"]):
            params["cabinets"] = "white_gloss"
        elif any(x in desc_lower for x in ["gris"]):
            params["cabinets"] = "grey_matte"
        elif any(x in desc_lower for x in ["antracita", "oscuro"]):
            params["cabinets"] = "anthracite"
        elif any(x in desc_lower for x in ["verde", "sage"]):
            params["cabinets"] = "sage_green"
        elif any(x in desc_lower for x in ["azul", "navy"]):
            params["cabinets"] = "navy_blue"
        elif any(x in desc_lower for x in ["negro"]):
            params["cabinets"] = "black_matte"

        # Detectar tiradores
        if any(x in desc_lower for x in ["sin tirador", "push", "gola"]):
            params["handles"] = "none"
        elif any(x in desc_lower for x in ["tirador negro", "tiradores negros"]):
            params["handles"] = "bar_black"
        elif any(x in desc_lower for x in ["dorado", "lat\u00f3n", "brass"]):
            params["handles"] = "bar_brass"
        elif any(x in desc_lower for x in ["cromado", "chrome"]):
            params["handles"] = "bar_chrome"

        # Detectar suelo
        if any(x in desc_lower for x in ["suelo roble", "parquet roble", "tarima"]):
            params["floor"] = "wood_oak"
        elif any(x in desc_lower for x in ["suelo nogal", "espiga"]):
            params["floor"] = "wood_walnut"
        elif any(x in desc_lower for x in ["azulejo blanco", "porcel\u00e1nico blanco"]):
            params["floor"] = "tile_white"
        elif any(x in desc_lower for x in ["azulejo gris", "porcel\u00e1nico gris"]):
            params["floor"] = "tile_grey"
        elif any(x in desc_lower for x in ["terracota", "barro"]):
            params["floor"] = "tile_terracotta"

        # Detectar estilo
        if any(x in desc_lower for x in ["minimalista", "minimal"]):
            params["style"] = "minimalist"
        elif any(x in desc_lower for x in ["industrial"]):
            params["style"] = "industrial"
        elif any(x in desc_lower for x in ["c\u00e1lido", "c\u00e1lida", "acogedor"]):
            params["style"] = "warm"
        elif any(x in desc_lower for x in ["revista", "magazine"]):
            params["style"] = "magazine"
        elif any(x in desc_lower for x in ["arquitect\u00f3nico"]):
            params["style"] = "architectural"

        # Lo que no se detectó se pasa como additional_details
        params["additional_details"] = description

        return params

    def detect_space_type(self, description: str) -> str:
        """Detecta QUÉ se quiere renderizar para no forzar siempre 'cocina'.

        Devuelve una frase en inglés lista para el prompt del modelo de imagen.
        """
        d = (description or "").lower()
        if any(x in d for x in ["armario", "empotrado", "ropero", "closet", "wardrobe", "vestidor", "walk-in", "walk in"]):
            return "fitted/built-in wardrobe (custom closet) with exterior doors and interior shelving, drawers and columns"
        if any(x in d for x in ["vitrina", "aparador", "cómoda", "comoda", "buffet", "sideboard"]):
            return "custom sideboard/cabinet furniture piece"
        if any(x in d for x in ["estanter", "librer", "bookcase", "shelving"]):
            return "custom shelving / bookcase unit"
        if any(x in d for x in ["baño", "bano", "aseo", "lavabo", "bathroom", "vanity"]):
            return "bathroom with custom vanity/cabinetry"
        if any(x in d for x in ["dormitorio", "habitaci", "bedroom"]):
            return "bedroom with custom furniture"
        if any(x in d for x in ["salón", "salon", "comedor", "living", "tv"]):
            return "living room with custom furniture"
        if any(x in d for x in ["cocina", "kitchen"]):
            return "modern kitchen"
        if any(x in d for x in ["mueble", "cabinet", "furniture", "puerta", "puertas"]):
            return "custom furniture / cabinetry piece"
        return "custom interior furniture / cabinetry piece"

    def build_render_prompt(
        self,
        description: str,
        style: str = "photorealistic",
        space_type: str = "custom interior furniture / cabinetry piece",
    ) -> str:
        """Prompt GENÉRICO dirigido por la descripción del usuario.

        A diferencia de build_kitchen_prompt (modo formulario de cocina), aquí la
        descripción del usuario es el contenido principal y NO se fuerza cocina.
        """
        style_instructions = {
            "photorealistic": "Ultra-photorealistic architectural interior photograph, indistinguishable from a real photo, shot on a full-frame DSLR with a 24-35mm lens, physically-based rendering (PBR), realistic global illumination and soft natural daylight coming from windows, accurate soft shadows, subtle reflections and ambient occlusion, true-to-life material micro-detail (visible wood grain, brushed metal, matte and satin finishes), neutral white balance, high dynamic range, fine 8K detail, shallow depth of field",
            "architectural": "Professional architectural visualization, clean lines, accurate proportions, realistic neutral daylight, PBR materials, soft realistic shadows",
            "magazine": "Interior design magazine photograph quality, professionally styled with tasteful accessories, warm inviting natural light, photorealistic PBR materials, editorial composition",
            "minimalist": "Clean minimalist photorealistic interior, uncluttered surfaces, zen-like simplicity, soft natural shadows, realistic matte materials",
            "warm": "Warm cozy photorealistic interior, golden-hour natural lighting, lived-in feeling, realistic textures and soft shadows",
            "industrial": "Industrial loft photorealistic interior, exposed materials, raw concrete and metal with realistic texture, dramatic but natural contrast lighting",
        }
        style_desc = style_instructions.get(style, style_instructions["photorealistic"])

        is_kitchen = "kitchen" in (space_type or "").lower() or "cocina" in (space_type or "").lower()
        # OJO: aquí ponía "base units ~90 cm high", que contradice lo que se
        # fabrica: el CASCO del bajo es de 80 y son el zócalo y la encimera los
        # que suben la altura de trabajo a 90-94. El criterio completo (oficio,
        # ergonomía, composición y qué hace vender una imagen) vive en
        # services/criterios_cocina.py para no tenerlo repartido.
        kitchen_scale = ""
        if is_kitchen:
            try:
                from services.criterios_cocina import CRITERIOS_RENDER_COCINA
                kitchen_scale = CRITERIOS_RENDER_COCINA
            except Exception:
                kitchen_scale = (
                    "Use real kitchen cabinetry scale: 80 cm base carcasses on a 10-15 cm "
                    "plinth so the worktop sits at 90-94 cm, wall units 70 or 90 cm tall "
                    "hung 55-60 cm above a continuous worktop of uniform thickness. "
                )

        parts = [
            f"{style_desc}.",
            f"Subject: a {space_type}.",
            f"Design brief (follow it precisely): {(description or '').strip()}",
            kitchen_scale,
            "Reproduce EXACTLY the elements described in the brief: the requested "
            "type of piece, exterior doors, finishes and colors, handles/pulls, "
            "materials, and the interior configuration (shelves, columns, drawers, "
            "open spaces) as specified.",
            "PER-MODULE FRONTS ARE MANDATORY: count the fronts of EACH cabinet exactly "
            "as stated. If a unit is described as '1 drawer + 2 gavetas (deep drawers)', "
            "render that unit with exactly one shallow drawer front on top and two deep "
            "drawer fronts below it — never replace it with a plain door or a different "
            "count. A module with drawers must show drawer fronts (horizontal seams with "
            "pulls), NOT a single full-height door.",
            "Camera angle: eye-level perspective showing the full piece within its space.",
            "Realism: photorealistic PBR materials with accurate roughness and reflectivity, "
            "realistic global illumination and contact shadows, true-to-scale proportions, "
            "natural color grading. It must look like a real photograph, NOT a 3D cartoon: "
            "avoid plastic-looking surfaces, flat lighting, oversaturated colors, blurry or "
            "low-detail textures, and any CGI/videogame look.",
            "Consistency: keep doors, drawers, shelves and handles straight, evenly spaced "
            "and aligned with the described layout; do not duplicate, merge, warp or omit "
            "modules; edges and lines must stay straight and in correct perspective.",
            "Do NOT invent or add appliances, fixtures, furniture, plants or decorative "
            "objects that are not explicitly mentioned in the brief above — if the brief "
            "does not mention an item, leave that space empty/clean rather than guessing.",
            "Composition: wide-angle shot in 16:9 landscape orientation, framing the full "
            "piece and its surrounding space from a corner.",
            "No text, watermarks, logos, people, or distorted/extra objects in the image.",
        ]
        if is_kitchen:
            parts.append(PRO_KITCHEN_DESIGN_PRINCIPLES)
        return " ".join(p for p in parts if p)

    async def _expand_brief(self, description: str, space_type: str) -> str:
        """Convierte el brief del usuario en una especificación de render DETALLADA
        y EXPLÍCITA usando un LLM potente (gemini-2.5-pro). Si falla, devuelve el
        brief original. Así el render obedece las órdenes con mucho más detalle."""
        desc = (description or "").strip()
        if not desc:
            return desc
        try:
            from services.llm_vision import generate_text_with_gemini
        except Exception:
            return desc
        instruction = (
            "Eres director de arte y prompt engineer de renders fotorrealistas de mobiliario "
            "y cocinas a partir de planos, bocetos y medidas. A partir del brief del cliente, "
            "redacta UNA especificación de render en INGLÉS, muy explícita y ordenada, que un "
            "modelo de imagen seguirá al pie de la letra para producir una FOTO profesional.\n"
            "REGLAS:\n"
            "- Conserva TODOS los detalles del cliente; no contradigas ni omitas nada de lo que pide.\n"
            "- NO inventes una cocina si el cliente no la pide (respeta el tipo de pieza/espacio). "
            "Si NO se menciona un elemento (electrodoméstico, isla, decoración…), NO lo añadas.\n"
            "- Enumera con precisión y en este orden: tipo de pieza/espacio; distribución "
            "(en L, en U, lineal, con isla…) y módulos de IZQUIERDA a DERECHA con su nº y tamaño "
            "de puertas/cajones/baldas/columnas; materiales y acabados exactos con su textura "
            "(veta de madera, vetas de piedra/cuarzo, lacas mate/satinadas); colores precisos; "
            "tiradores; encimera (material, grosor y canto) y copete/frontal; electrodomésticos "
            "integrados; zócalo; suelo; paredes; iluminación; ambiente; y ángulo de cámara.\n"
            "- Si es una COCINA, especifica proporciones reales: bajos ~90 cm con zócalo "
            "retranqueado, altos a ~55-60 cm sobre la encimera, encimera continua de grosor "
            "uniforme, electrodomésticos enrasados con los frentes y juntas/holguras regulares.\n"
            "- Respeta SIEMPRE las medidas/proporciones si se dan; no las cambies. Termina con "
            "instrucciones de fotorrealismo (materiales PBR, luz natural, sombras y reflejos "
            "reales) y un breve prompt negativo (nada de aspecto cartoon/CGI, plástico, "
            "geometría deformada, módulos duplicados, texto, marcas de agua ni personas).\n"
            f"- Tipo de pieza/espacio detectado: {space_type}.\n\n"
            f"BRIEF DEL CLIENTE:\n{desc}\n\n"
            "Devuelve SOLO la especificación de render (sin encabezados ni explicaciones)."
        )
        try:
            expanded = await generate_text_with_gemini(instruction, model="gemini-2.5-pro")
        except Exception as e:
            logger.warning(f"_expand_brief falló: {e}")
            return desc
        return expanded.strip() if expanded else desc

    async def generate_render(
        self,
        description: str,
        params_override: Optional[Dict[str, Any]] = None,
        reference_image: Optional[str] = None,
        reference_mime: Optional[str] = None,
        provider: Optional[str] = None,
        reference_images: Optional[list] = None,
        project_type: Optional[str] = None,
        room_photo: bool = False,
        editing_render: bool = False,
    ) -> Dict[str, Any]:
        """
        Genera un render 3D a partir de una descripción (texto o voz transcrita).

        Args:
            description: Descripción en lenguaje natural
            params_override: Parámetros explícitos que sobreescriben el parsing
            reference_image: Imagen/PDF de referencia (base64) que el modelo debe
                respetar (distribución, proporciones, medidas).
            reference_mime: MIME de la imagen de referencia.

        Returns:
            Dict con el resultado del render
        """
        # Parsear descripción natural
        parsed_params = self.parse_natural_language(description)

        # Aplicar overrides si los hay
        if params_override:
            parsed_params.update(params_override)

        # Tipo de espacio: si el usuario ELIGIÓ un tipo de proyecto (Cocina,
        # Armario, Baño…), MANDA sobre la detección por texto — así una plantilla
        # de cocina no puede acabar generando un armario. Solo "otro" delega en
        # la detección automática por la descripción.
        _forced = {
            "cocina": "modern kitchen",
            "armario": "fitted/built-in wardrobe (custom closet) with exterior doors and interior shelving, drawers and columns",
            "bano": "bathroom with custom vanity/cabinetry",
        }
        pt = (project_type or "").strip().lower()
        if pt in _forced:
            space_type = _forced[pt]
        else:
            space_type = self.detect_space_type(description)
        parsed_params["space_type"] = space_type

        # Preparar la referencia. IA0 conserva los 150 dpi históricos; IA7 usa
        # más detalle para que cotas y trazos finos sobrevivan al rasterizado.
        dpi_referencia = 280 if provider == "julio11_plus" else 150
        ref_b64, ref_mime = self._prepare_reference(
            reference_image, reference_mime, pdf_dpi=dpi_referencia)
        parsed_params["hasReference"] = bool(ref_b64)

        # ── CON REFERENCIA = edición / re-render FIEL ──────────────────────────
        # La imagen manda. NO expandimos el brief ni inyectamos principios de
        # diseño (harían que el modelo REDISEÑE en vez de mantener la cocina y
        # aplicar solo el cambio pedido, p. ej. el color de las puertas).
        # EXCEPCIÓN: si la referencia es un CROQUIS/PLANO MANUSCRITO (PDF escaneado
        # o imagen con trazos a mano), NO es una foto a editar sino un plano del que
        # INTERPRETAR la distribución. En ese caso usamos la rama SIN referencia pero
        # pasando la imagen como guía de layout. (Si room_photo es True, NUNCA es croquis: es la estancia real).
        #
        # `editing_render` es la MISMA idea y por el mismo motivo: cuando el ERP
        # edita SU PROPIO render, ya sabe lo que es y no hay nada que adivinar.
        # Sin esto se le pasaba el render al detector de croquis, y una cocina
        # blanca —paredes blancas, muebles blancos, encimera blanca— tiene poco
        # color y mucho claro, que es justo la firma del papel. La tomaba por un
        # dibujo y se iba por la rama de «construye lo que está dibujado»: en vez
        # de cerrar las puertas que se le pedían, REHACÍA la cocina entera y
        # devolvía otra distinta (puertas convertidas en gavetas, altos movidos).
        # No daba ningún error: devolvía una cocina preciosa que no era la suya.
        # Una procedencia conocida siempre gana a una heurística.
        is_sketch = False if (room_photo or editing_render) else \
            self._is_sketch_reference(reference_image, reference_mime)

        # ── AMUEBLADO VIRTUAL: la foto es la ESTANCIA REAL (vacía / a reformar) ──
        # No hay que EDITAR un mueble existente, sino DISEÑAR uno nuevo DENTRO de esa
        # estancia respetando su arquitectura (paredes, ventanas, puertas, suelo,
        # techo, perspectiva y luz reales). Cierra ventas: el cliente ve su propio hueco.
        if ref_b64 and room_photo:
            pt2 = (project_type or "").strip().lower()
            pieza = {"armario": "fitted wardrobe/closet", "bano": "bathroom vanity/cabinetry"}.get(pt2, "kitchen")
            parsed_params["briefExpanded"] = False
            parsed_params["virtualStaging"] = True
            task_prompt = (
                f"The attached photo is a REAL ROOM of the client (it may be EMPTY, being "
                f"renovated, or STILL HAVE AN OLD {pieza} installed). Your job is to show this "
                f"same room fitted with a BRAND-NEW {pieza}. "
                "IF THE ROOM ALREADY HAS furniture/cabinets/appliances/worktop, REMOVE all of that "
                "existing (old) furniture completely and REPLACE it with the newly designed one — "
                "do NOT keep the old units, do not leave them behind and do not stack the new "
                "design on top of them. "
                "Keep the room's ARCHITECTURE strictly unchanged: the same walls, corners and room "
                "shape, the SAME windows and doors at their real position and size, the SAME "
                "ceiling, and the SAME camera viewpoint, perspective and vanishing lines as the "
                "photo. Match the real lighting and the direction of the natural light coming from "
                "the windows. Integrate the new furniture realistically against the real walls "
                "(respect the free wall lengths available). You MAY update floor and wall finishes "
                "if the brief asks, but never move or resize the openings or change the room's "
                "proportions.\n\n"
                "EXISTING INSTALLATIONS (very important, so the kitchen is BUILDABLE without moving "
                "plumbing or wiring): look at the photo for existing points — water supply / tap, "
                "drain, wall sockets, gas outlet, radiator and the boiler if visible — and DESIGN "
                "AROUND them: place the sink and dishwasher where the water/drain already are, the "
                "hob near its supply, and keep the fridge/oven near existing sockets. Do NOT invent "
                "a layout that would require relocating those installations.\n\n"
                f"Furniture to design (finishes, materials, colors, layout): {description or 'cocina moderna funcional'}.\n\n"
                "Photorealistic result, PBR materials, realistic shadows and reflections coherent "
                "with the room's light, 16:9. It must look like a real photo of THIS room, now "
                "furnished. No text, watermarks or logos."
            )
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider=provider,
            )
        # ── IA 7: IA0 + GEOMETRÍA/VANOS Y REFERENCIA DE MAYOR CALIDAD ────────
        # IA0 permanece congelada. IA7 reutiliza su ampliación y constructor,
        # añadiendo únicamente las reglas estructurales del 22/07.
        if ref_b64 and is_sketch and provider == "julio11_plus":
            from services.luiggi_ai.render_22jul import (
                build_render_prompt as _brp_ia7, prompt_del_croquis_22jul)
            parsed_params["motor"] = "IA 7 — IA0 con lectura mejorada"
            parsed_params["fromSketch"] = bool(is_sketch)
            _brief = await self._expand_brief(description, space_type)
            parsed_params["briefExpanded"] = bool(_brief) and _brief != (description or "").strip()
            _generico = _brp_ia7(
                description=_brief or description,
                style=parsed_params.get("style", "photorealistic"),
                space_type=space_type,
            )
            task_prompt = prompt_del_croquis_22jul(
                _generico, hay_referencia=True, es_croquis=True)
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider="julio11_plus", reference_images=reference_images or None,
            )

        # ── IA 0: EL CAMINO DEL 11 DE JULIO, TAL CUAL ─────────────────────────
        #
        # Botón de comparación histórica. Conserva el encargo de croquis anterior
        # a los cambios de agosto y fuerza el primer modelo de imagen que estaba
        # en producción el 11/07/2026. IA1 y sus reglas actuales no se modifican.
        if ref_b64 and is_sketch and provider == "julio11":
            from services.luiggi_ai.render_11jul import (
                build_render_prompt as _brp_11jul, prompt_del_croquis_11jul)
            parsed_params["motor"] = "IA 0 — camino del 11/07/2026"
            parsed_params["fromSketch"] = bool(is_sketch)
            # En julio el brief se expandía con Gemini 2.5 Pro antes de montar
            # el prompt de imagen. Se conserva para medir el mismo camino.
            _brief = await self._expand_brief(description, space_type)
            parsed_params["briefExpanded"] = bool(_brief) and _brief != (description or "").strip()
            _generico = _brp_11jul(
                description=_brief or description,
                style=parsed_params.get("style", "photorealistic"),
                space_type=space_type,
            )
            task_prompt = prompt_del_croquis_11jul(
                _generico, hay_referencia=True, es_croquis=bool(is_sketch))
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider="julio11", reference_images=reference_images or None,
            )

        # ── IA 5: EL CAMINO DEL 10 DE JULIO, TAL CUAL ─────────────────────────
        #
        # El master, tras cuatro renders seguidos de la misma cocina: «busca lo
        # que hacía el 10 de julio de 2026, que funcionaba mejor»; luego «podías
        # poner un botón de IA 5, con el prompt del 10 de julio»; y después,
        # «podemos poner en IA 5 lo que hacía el programa el 22 de julio». El 22
        # es el bueno: añade los VANOS —ventana y puerta en su sitio— y la
        # frase que lo cierra, «la geometría viene 100% del dibujo».
        #
        # Tiene razón en el método. Trece rondas de yo apretando el encargo y él
        # diciendo que no se parece no las zanja otra teoría mía: las zanja
        # rendir el MISMO croquis por los dos caminos y mirar las dos imágenes.
        #
        # Va ANTES de la rama de hoy y a propósito NO lleva nada de agosto: ni
        # recorte del dibujo dentro de la página, ni lectura a ficha, ni lista
        # de módulos numerada. En julio no existían. Un botón «julio con los
        # arreglos de agosto» no contestaría a la pregunta.
        # ...PERO SOLO CUANDO LA REFERENCIA ES UN DIBUJO.
        #
        # Aqui la lie ayer. Puse esta rama ANTES que la de edicion para que IA 5
        # se disparase pasara lo que pasara, y con eso se trago TODAS las
        # ediciones: el master, «cuando le doy al boton de decorador/a, cambia
        # el diseño totalmente con la IA 5».
        #
        # Y era exacto. El boton de Decorador manda el render con la orden «NO
        # cambies NADA del mobiliario, solo el ambiente». Con IA 5 puesta, esa
        # orden ni se leia: la imagen entraba por el camino de julio, que trata
        # lo que le llega como UN PLANO QUE HAY QUE REALIZAR DESDE CERO. Salia
        # otra cocina. Lo mismo le pasaba a HD, a «aplicar cambio» y a los
        # planos tecnicos.
        #
        # `is_sketch` es justo la pregunta que faltaba: ¿esto es un dibujo o es
        # una foto que hay que retocar? Cuando es una foto, esta rama se aparta
        # y la edicion sigue su camino de siempre.
        if ref_b64 and is_sketch and provider == "julio":
            from services.luiggi_ai.render_22jul import (
                build_render_prompt as _brp_22jul, prompt_del_croquis_22jul)
            parsed_params["motor"] = "IA 5 — camino del 22/07/2026"
            parsed_params["fromSketch"] = bool(is_sketch)
            # En julio el croquis pasaba por `_expand_brief` (gemini-2.5-pro),
            # que redacta una especificación entera SIN haber visto el dibujo.
            # Va incluido porque iba: quitarlo sería otra cosa, no julio.
            _brief = await self._expand_brief(description, space_type)
            parsed_params["briefExpanded"] = bool(_brief) and _brief != (description or "").strip()
            _generico = _brp_22jul(
                description=_brief or description,
                style=parsed_params.get("style", "photorealistic"),
                space_type=space_type,
            )
            task_prompt = prompt_del_croquis_22jul(
                _generico, hay_referencia=True, es_croquis=bool(is_sketch))
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider="gemini", reference_images=reference_images or None,
            )


        if ref_b64 and not is_sketch:
            change = (description or "").strip()
            parsed_params["briefExpanded"] = False
            # Si además llegan imágenes de ELEMENTO (una puerta, un mueble a copiar),
            # se lo indicamos al modelo para que incorpore ESE elemento a la cocina.
            extra_imgs = [i for i in (reference_images or []) if i]
            elemento_note = ""
            if extra_imgs:
                elemento_note = (
                    "\n\nADDITIONAL reference image(s) are provided AFTER the main one: they show a "
                    "specific ELEMENT (e.g. a door front, a handle, a cabinet or appliance) that you "
                    "must ADD to / replicate in the kitchen, matching its look, color and finish, and "
                    "placing it coherently. The FIRST image is always the existing kitchen to keep."
                )
            task_prompt = (
                "You are given a reference image of an EXISTING kitchen/furniture design.\n\n"
                "THE CONTRACT HAS TWO HALVES, AND BOTH SE CUMPLEN:\n"
                f"  (A) THE REQUESTED CHANGE — DO IT, COMPLETELY: {change or 'nothing; just re-render faithfully'}\n"
                "  (B) EVERYTHING THE REQUEST DOES NOT MENTION — leave exactly as it is.\n\n"
                "(A) WINS INSIDE ITS OWN SCOPE. If the request asks to ADD, REMOVE, WIDEN, NARROW "
                "or MOVE a unit, then doing it is the job: add the unit, and shift or resize the "
                "NEIGHBOURING units of that same run just enough to make room, keeping their order. "
                "'Keep everything identical' never means refusing the change; it means not touching "
                "the other walls, the appliances, the finishes, the room or the camera.\n\n"
                "(B) IS THE REST, AND SE RESPETA AL MILÍMETRO: the SAME layout and room shape, the "
                "SAME modules (number, order, position and size) everywhere the request does not "
                "touch, the SAME appliances in the same places, the SAME sink, hob, hood, windows "
                "and doors, and the SAME camera angle, framing and perspective. Do NOT redesign, "
                "reorganize, add, remove, move, resize or 'improve' anything the request is silent "
                "about."
                + elemento_note + "\n\n"
                "MEASUREMENTS IN THE REQUEST ARE EXACT, ESPECIALLY THE NARROW ONES:\n"
                "- A width given in cm is that width. A 15 cm unit is 15 cm: a SLIM vertical strip, "
                "roughly a quarter the width of a 60 cm unit next to it. Bottle racks, spice "
                "pull-outs and fillers of 15, 20 or 30 cm are ordinary kitchen units, not mistakes.\n"
                "- NEVER widen a narrow unit to make it look better balanced, and never merge it "
                "into the unit beside it or drop it because it seems too thin to draw. If the "
                "request says 15 cm, a 15 cm unit must be clearly visible in the finished image.\n"
                "- A pull-out / 'extraíble' / bottle unit is rendered CLOSED, as a single tall "
                "narrow front, usually with a slim handle or gola — not as an open basket.\n\n"
                "THE FRONTS OF EACH MODULE DO NOT CHANGE (except where the request says otherwise):\n"
                "- Every module keeps the SAME KIND and NUMBER of fronts it already has. A module "
                "with two hinged DOORS keeps two hinged doors; a module with drawers keeps exactly "
                "those drawers. NEVER swap doors for drawers or drawers for doors, and never change "
                "how many fronts a module has, unless the requested change says so in those words.\n"
                "- 'Close the doors' / 'cierra las puertas' means render those SAME doors in their "
                "CLOSED position. It does NOT mean remove them, replace them with drawers or a "
                "solid panel, or rebuild the module. Same doors, same size, same hinges, shut.\n"
                "- Words about the STATE of something (open/closed, on/off, light/dark) change only "
                "that state. They never authorise changing the furniture itself.\n\n"
                "Photorealistic result, realistic PBR materials, natural light and shadows, 16:9. "
                "It must look like the SAME kitchen as the reference, WITH the requested change "
                "actually carried out. No text, watermarks or logos."
            )
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider=provider, reference_images=extra_imgs or None,
            )

        # ── CROQUIS / PLANO A MANO = el DIBUJO manda ───────────────────────────
        # El croquis NO puede compartir camino con «diseñar desde cero». Ahí se
        # llama a `_expand_brief`, que le pide a un LLM que redacte la
        # distribución y los módulos de izquierda a derecha **a partir del texto
        # y SIN haber visto el dibujo**. Esa especificación inventada acaba
        # ocupando casi todo el prompt, y el modelo de imagen la obedece a ella
        # en vez de al croquis: sale una cocina genérica que no es la del
        # cliente. Es lo mismo que ya estaba escrito en el render compuesto —
        # «un texto largo de dirección de arte compite con las imágenes» — pero
        # aquí no se había aplicado.
        #
        # Con un croquis delante, el prompt va CORTO y centrado en el dibujo, y
        # el texto se queda solo con lo suyo: acabados, materiales y colores.
        if ref_b64 and is_sketch:
            parsed_params["briefExpanded"] = False
            parsed_params["fromSketch"] = True
            # LA DISTRIBUCIÓN LA MANDA EL DIBUJO, Y LA PANTALLA TIENE QUE DECIRLO.
            #
            # La pantalla arranca con `layout: 'L-shape'` escrito a fuego y lo
            # manda en cada petición. Con un croquis delante eso no lo decide
            # nadie: lo decide el dibujo. Pero el pie del render seguía pintando
            # «Layout: L-shape» — el master vio eso justo debajo de una cocina
            # LINEAL, con la palabra «Cocina lineal» impresa en su referencia.
            # No cambiaba el render (este valor no entra en el prompt), pero un
            # dato falso en pantalla se cree, y encima manda a buscar el fallo
            # donde no está.
            parsed_params["layout"] = "según el dibujo"
            brief_txt = (description or "").strip()

            # QUÉ MUEBLE ES. El prompt decía «kitchen» siempre, escrito a fuego:
            # con el croquis de un armario se le pedía al modelo una COCINA y
            # luego se le exigía fidelidad al dibujo. Órdenes contradictorias.
            _pieza = {
                "armario": "fitted wardrobe / walk-in closet",
                "bano": "bathroom vanity / cabinetry",
            }.get((project_type or "").strip().lower(), "kitchen")

            # UN ARMARIO NO SE LEE NI SE ENCARGA COMO UNA COCINA.
            #
            # Decir «esto es un armario» en una línea y seguir con mil palabras
            # de cocina —el hueco de la campana sobre la placa, la encimera que
            # muere contra la columna, el diccionario de Frigo / Combi /
            # Lavavajillas / Bajo Fregadero— son órdenes contradictorias, y el
            # modelo se queda con las mil palabras. El master mandó un armario
            # de DOS cuerpos con altillo corrido y una cajonera abajo a la
            # izquierda: volvió un frente de SEIS módulos con la cajonera en el
            # centro. Esa es la composición de una cocina, no de su armario.
            #
            # Desde aquí, el croquis de armario tiene su propio lector y su
            # propio encargo. El camino de cocina no se toca: es el que lleva
            # años funcionando y no se arregla un módulo rompiendo el otro.
            from services.luiggi_ai.render_armario import (
                es_armario as _es_armario, prompt_croquis_armario)
            if _es_armario(project_type, space_type):
                return await self._render_croquis_de_armario(
                    ref_b64=ref_b64, ref_mime=ref_mime, brief_txt=brief_txt,
                    parsed_params=parsed_params, provider=provider,
                    reference_images=reference_images,
                    prompt_croquis_armario=prompt_croquis_armario,
                )

            # EL DIBUJO, A PANTALLA COMPLETA.
            #
            # El master sube el pantallazo del móvil de una página de
            # presupuesto: barra de estado, título, marca, EL DIBUJO, tres
            # líneas de precios, el total y la barra de Android. La cocina ocupa
            # un tercio de la altura.
            #
            # Se le puede decir mil veces al modelo que se fije en los frentes:
            # si en la imagen que recibe la cocina es pequeña, el detalle fino
            # —los altos partidos en dos filas, el nicho de la campana, las
            # divisiones de cada frente— NO SE VE. Esto no es otra regla de
            # prompt; es darle la cocina entera de lado a lado.
            #
            # Recorta solo cuando lo tiene claro (ver `recorte_croquis`): ante
            # la duda devuelve la original, porque un recorte torcido se
            # llevaría media cocina y el render seguiría saliendo bonito.
            try:
                from services.recorte_croquis import recortar_dibujo_base64
                recortado, hubo_recorte = recortar_dibujo_base64(ref_b64, ref_mime)
                if hubo_recorte:
                    ref_b64, ref_mime = recortado, "image/png"
                    parsed_params["dibujoRecortado"] = True
                    logger.info("Croquis recortado de la página: el dibujo va a pantalla completa.")
            except Exception as e:
                logger.warning(f"No se pudo recortar el croquis, se usa la imagen entera: {e}")

            # EL DIBUJO SE LEE A FICHA, NO A REDACCIÓN.
            #
            # Cuatro veces seguidas el master dijo lo mismo del mismo render, y
            # cuatro veces se apretó el encargo con más reglas. Volvía a faltar
            # siempre lo mismo: los altillos y el nicho de la campana. El fallo
            # no estaba en las reglas, estaba en el camino:
            #
            #     dibujo -> párrafo en prosa -> modelo de imagen
            #
            # Un párrafo no se cuenta. «Una fila de altos con altillos encima»
            # describe igual de bien cinco que tres. Lo que no sobrevive a la
            # prosa son los NÚMEROS. Ahora se lee a lista de muebles y el
            # encargo lo escribimos nosotros, numerado y contable.
            #
            # Si la lectura a ficha no sale (el modelo devuelve prosa, o basura),
            # se cae a la transcripción de siempre. Perder el detalle es malo;
            # quedarse sin render es peor.
            lectura = await self._leer_cocina_del_dibujo(ref_b64, ref_mime)
            if lectura:
                from services.luiggi_ai.lectura_cocina import (
                    especificacion_en_texto, relacion_mv, resumen_para_pantalla)
                sketch_transcription = especificacion_en_texto(lectura)
                parsed_params["lecturaDelDibujo"] = resumen_para_pantalla(lectura)
                parsed_params["lecturaEstructurada"] = True
                # LA MISMA LECTURA, EN NOTACIÓN MV, PARA PEGARLA EN EL
                # PRESUPUESTO. El resumen de arriba es para leerlo; el pegado
                # masivo de Cocina Montada 3 y Cocina Desmontada habla otra
                # lengua («1 bf60 (altura 80)»). Se genera aquí para que salga
                # de la MISMA lectura y no de una segunda interpretación.
                _rel = relacion_mv(lectura)
                if _rel.get("texto"):
                    parsed_params["relacionMV"] = _rel["texto"]
                    parsed_params["relacionMVLineas"] = _rel["lineas"]
                    parsed_params["relacionMVSinAncho"] = _rel["sin_ancho"]
                    parsed_params["relacionMVCajoneras"] = _rel["cajoneras"]
            else:
                sketch_transcription = await self._transcribe_sketch_with_vision(ref_b64, ref_mime)
                parsed_params["lecturaEstructurada"] = False
                # QUE SE CAIGA AL MÉTODO VIEJO NO PUEDE SER INVISIBLE.
                #
                # El master mandó un render y debajo no salía el recuadro de «leído
                # del dibujo». No salía porque la lectura a ficha había fallado y se
                # había caído a la de prosa —en silencio—. Desde fuera eso se ve
                # exactamente igual que si la mejora no estuviera desplegada: uno se
                # queda mirando una pantalla que no dice nada y sacando conclusiones
                # sobre la versión equivocada.
                #
                # El respaldo está bien: quedarse sin render sería peor. Lo que no
                # puede es no notarse.
                parsed_params["lecturaDelDibujo"] = (
                    "No se ha podido leer el plano a ficha (módulos y cotas uno a uno). "
                    "Se ha usado la lectura antigua, en prosa: el render puede perder la "
                    "cuenta de módulos y las medidas. Vuelve a intentarlo, o sube el plano "
                    "más grande y recortado."
                )
            transcription_block = f"\nTECHNICAL BREAKDOWN EXTRACTED DIRECTLY FROM THE SKETCH:\n{sketch_transcription}\n" if sketch_transcription else ""

            task_prompt = (
                f"You are given a TECHNICAL 2D DRAWING of ONE specific {_pieza}: a floor plan, "
                "elevation or blueprint. It may be hand-drawn with handwritten dimensions, or a "
                "printed line drawing (CAD / catalogue style).\n"
                "ONLY THE DRAWING COUNTS. The image may be a PHONE SCREENSHOT OF A WHOLE PAGE: a "
                "title, a brand box, priced line items, totals, buttons and the phone's own status "
                "and navigation bars can surround the drawing. All of that is packaging — never "
                "render it, never let it crop your attention, and never treat a price line or a "
                "brand name as a piece of furniture. Find the drawing inside the page and work from "
                "it alone. The ONE thing worth reading in that surrounding text is the SHAPE of the "
                "job if it is stated ('Cocina lineal' = straight single-wall run, 'en L', 'en U'): "
                "that confirms the layout, it never overrides what is drawn.\n"
                + transcription_block +
                f"Produce a single photorealistic interior photograph of THAT SAME {_pieza}, "
                "built exactly as drawn. This is a FAITHFUL 3D realisation of the drawing, "
                "NOT a new design — do not 'improve' it and do not substitute a nicer layout.\n\n"
                "THE DRAWING GIVES GEOMETRY. IT NEVER GIVES STYLE:\n"
                "- The output is a PHOTOGRAPH of real furniture in a real room. It is never a "
                "drawing, illustration, cartoon, comic, sticker, clip-art, flat vector, cel-shaded "
                "or hand-painted image, and never a 'render of a drawing'.\n"
                "- Copy from the reference ONLY: what modules exist, their order, their sizes and "
                "what goes inside each one. Copy NOTHING of how it is drawn — no outlines or "
                "contour lines around objects, no flat fills, no paper texture, no sketchy edges, "
                "no pastel illustration palette, no uniform lighting.\n"
                "- The colours of the drawing are NOT the materials. A cabinet drawn in flat pale "
                "blue or beige is a cabinet whose finish comes from the brief text; if the brief "
                "says nothing, use restrained real materials (matt lacquer, natural oak veneer).\n"
                "- Everything drawn inside must become the REAL object photographed: garments in "
                "real fabric with real folds, real leather shoes, real cardboard or fabric boxes, "
                "real metal rails and hangers. Never a drawing of a shirt — an actual shirt.\n"
                "- Real photography: physically based materials, visible wood grain and textile "
                "weave, contact shadows under every object, soft directional daylight, shallow "
                "natural falloff into the corners.\n\n"
                "CLOSED COMPOSITION — THIS IS THE RULE THAT OVERRIDES THE OTHERS:\n"
                "- The kitchen contains EXACTLY the modules that are drawn or written, and NOTHING ELSE. "
                "Never add a module because a kitchen 'usually' has one there — no extra fridge, combi, "
                "larder, broom unit, wine cooler or filler cabinet. If it is not drawn or written, IT DOES "
                "NOT EXIST and it must NOT appear in the image.\n"
                "- NEGATIONS ARE ORDERS TOO. If the text says something is NOT there ('no va combi', "
                "'sin campana', 'no lleva columna', 'only a side panel'), that item MUST NOT be rendered. "
                "A word appearing inside a negative sentence is a PROHIBITION, never a request. Read the "
                "whole sentence before rendering anything named in it.\n"
                "- A run of cabinets ENDS where the drawing ends. If the drawing shows only a side panel, "
                "an end panel or a bare wall past the last module, render exactly that: a side panel or "
                "empty wall. Do not close the run with an invented cabinet or column.\n"
                "- Empty wall is a valid, correct result. Leave it empty.\n\n"
                "FRONT-BY-FRONT FIDELITY — A MODULE IS NOT A BOX, IT IS ITS FRONTS:\n"
                "- Reproduce, module by module, the EXACT number of fronts drawn on its face and the EXACT kind of each one. "
                "Count every horizontal and vertical dividing line on the face of each unit: a unit drawn with three stacked "
                "fronts is THREE DRAWERS, not one door; a unit drawn with a vertical line down the middle is TWO side-by-side doors.\n"
                "- NEVER merge two drawn fronts into a single flat panel, and never split a single drawn front into several. "
                "A single plain door where the drawing shows a bank of drawers is a WRONG kitchen, not a simplification.\n"
                "- A tall column drawn with a horizontal division is TWO stacked doors (or a door plus an appliance), not one full-height door.\n"
                "- Drawers must read as drawers in the photograph: a continuous horizontal reveal across the full width of the unit, "
                "aligned with the reveals of the neighbouring units, and the gola channel or handle repeated on EVERY drawer front.\n"
                "- Reveals and joints line up across the whole run: the horizontal lines of the fronts are continuous from module to module, "
                "exactly as drawn. Misaligned or randomly placed joints are wrong.\n\n"
                "A GAP IN THE WALL UNITS IS PART OF THE DESIGN, NOT A MISTAKE:\n"
                "- If the row of wall cabinets is interrupted — typically above the hob, where only the extractor hood goes — "
                "that opening MUST appear in the photograph, at the same place and the same width. Do NOT fill it with an invented "
                "cabinet, and do NOT stretch the neighbouring units to close it. Bare wall above the hob with the hood on it is the correct result.\n\n"
                "HEIGHTS ARE DRAWN TOO — A TALL COLUMN IS TALLER, AND IT SHOWS:\n"
                "- Reproduce the RELATIVE HEIGHTS exactly as drawn. A block drawn taller than its "
                "neighbours is taller in the photograph: full-height columns normally start at the "
                "floor and rise ABOVE the top line of the wall cabinets, often to the ceiling. "
                "Never level everything to one height, and never shrink a full-height column down "
                "to the height of a wall unit.\n"
                "- A full-height column touches the floor. If the drawing shows a block running "
                "uninterrupted from the floor line to above the wall units, it is ONE tall column, "
                "not a base unit with a separate wall unit above it, and no countertop crosses it.\n"
                "- The countertop stops where the column starts, butting against its side panel.\n"
                "- WALL CABINETS CAN BE TWO STACKED ROWS. If the drawing shows the upper band divided by a "
                "horizontal line into two rows of boxes, that is a row of wall units with a second row of "
                "shorter units (altillos) ON TOP, normally running right up to the ceiling. Render BOTH rows, "
                "with the horizontal joint between them, and take them up to the ceiling as drawn. One single "
                "row floating with bare wall above it is a DIFFERENT kitchen and is wrong.\n"
                "- The top line of the wall cabinets is where the drawing puts it: if the units reach the "
                "ceiling, they reach the ceiling; if they stop short, they stop short. Do not invent a gap.\n\n"
                "STRAIGHT SINGLE-WALL RUN — CAMERA:\n"
                "- If the drawing is a LINEAR run against one single wall (no corner, no return, no "
                "island), photograph it close to straight-on / slightly off-axis so the WHOLE run "
                "reads from end to end. A steep three-quarter angle is wrong here: it foreshortens "
                "the far end until the last modules disappear. The three-quarter corner view is "
                "only for L, U and peninsula layouts.\n\n"
                "BOTH ENDS OF THE RUN MUST BE IN THE PHOTOGRAPH:\n"
                "- The LAST MODULE ON THE RIGHT and the LAST MODULE ON THE LEFT are as important as the middle ones. "
                "The kitchen ends exactly where the drawing ends: render every module up to and including the one at each extreme edge.\n"
                "- FRAME THE SHOT SO NOTHING IS CUT OFF. Pull the camera back until the complete run fits inside the frame with a "
                "margin of empty room on both sides. Never crop a module at the edge of the image, never let the last unit on the right "
                "fall outside the frame, and never zoom into the centre of the kitchen. If the whole kitchen does not fit, widen the "
                "lens — do not drop a module.\n\n"
                "THE DRAWING IS THE GROUND TRUTH FOR GEOMETRY:\n"
                "- Reproduce the EXACT overall SHAPE of the kitchen (linear, L-shaped, U-shaped, "
                "with island or peninsula) as drawn. If it is drawn as an L, it must be an L.\n"
                "- PHYSICAL L-SHAPE RULE: when the drawing has a 90-degree corner, a visible return, or modules continuing onto a secondary wall, render TWO PERPENDICULAR cabinet runs joined at that inside corner. Never flatten the return wall into the main frontal run. The final image must visibly show the depth and receding side wall of the L.\n"
                "- Reproduce the EXACT NUMBER and ORDER of the modules from left to right: base units, wall units and tall columns.\n"
                "- EXACT TALL COLUMN COUNT: render PRECISELY the number of tall columns drawn in the sketch. If ONLY 1 single column is drawn on the right, render EXACTLY 1 column (do NOT invent a 2nd or 3rd column). If 2 or 3 columns are drawn, render each one as drawn.\n"
                "- APPLIANCE PLACEMENT FROM SKETCH: place every sink and cooktop on the EXACT module where drawn (e.g. if sink is on module 2 and cooktop is on module 3, keep that exact sequence).\n"
                "- NON-NEGOTIABLE APPLIANCE PRESERVATION: every appliance drawn, outlined, circled or labelled in the sketch MUST appear as that SAME visible appliance in the SAME module and left-to-right order. Never replace an appliance with a generic cabinet, blank door, drawer, shelf or empty gap.\n"
                "- HANDWRITTEN FINISH LABELS ON DRAWING: read handwritten material labels on the drawing:\n"
                "  · 'NEGRO' on/near upper units: render upper wall cabinets in solid matte black.\n"
                "  · 'MADERA' on/near lower units: render base cabinets in warm natural oak wood grain.\n"
                "  · 'NEGRO' / 'BLANCO' / 'MADERA': apply the specified finish to the exact cabinet group indicated.\n"
                "- CONTINUOUS STRAIGHT BACK WALL (LINEAR LAYOUT): in a linear elevation, every single base cabinet, wall unit and tall column is installed against ONE SINGLE FLAT CONTINUOUS BACK WALL in a single unbroken flush line. The countertop must end directly abutting against the vertical side panel of the oven tower column.\n"
                "- DOORS AND DRAWERS MUST BE FULLY CLOSED: every single cabinet door, drawer, pull-out unit and lift-up flap MUST be rendered 100% COMPLETELY CLOSED and flush in its resting position.\n"
                "- READ HANDWRITTEN SPANISH TECHNICAL LABELS AND CODES. This is a DICTIONARY, not a "
                "shopping list: each entry applies ONLY when that label is actually written on the "
                "drawing (or stated affirmatively in the text) AND is not negated. Never render an item "
                "just because its name appears in this list:\n"
                "  · 'Frigo' / 'Frijo' / 'Frigorifico': render a DISTINCT, VISIBLE freestanding refrigerator exactly where drawn, with the appliance front exposed (never concealed by kitchen doors).\n"
                "  · 'Combi': render a DISTINCT, VISIBLE freestanding combi refrigerator with exposed appliance front and clear upper/lower door split, exactly in the module drawn.\n"
                "  · 'Combi integrable' / 'Frigo integrable': render an INTEGRATED combi refrigerator concealed behind kitchen cabinet doors, with fronts matching the exact colour, material, gola and handle system of the kitchen.\n"
                "  · 'Side by side': render one DISTINCT, VISIBLE freestanding American-style side-by-side refrigerator, with exposed appliance finish and two full-height vertical doors, exactly in the drawn location.\n"
                "  · 'Side by side integrable': render a 120cm INTEGRATED side-by-side refrigerator made of TWO 60cm-wide full-height integrated fridge columns, each concealed behind matching kitchen doors; never show an exposed appliance front.\n"
                "  · 'Micro / Horno' or 'Micro' + 'Horno': tall column tower with built-in electric oven and built-in microwave directly above it in the same column.\n"
                "  · 'Columna' / '70' (Despensero): tall 70cm storage column at the far right with 4 distinct doors (2 upper doors side-by-side and 2 lower doors side-by-side).\n"
                "  · 'Campana Cristal Inclinada' / 'Campana Inclinada Negra': render a modern ANGLED BLACK GLASS wall-mounted extractor hood centered above the cooktop, with no cabinets directly above the hob.\n"
                "  · 'Abatible' / 'Abatibles': horizontal lift-up / bi-fold wall cabinet doors, rendered neatly CLOSED with subtle horizontal reveal gap.\n"
                "  · 'Puerta Integr. LVV' / 'LVV' / 'Lavavajillas integrable': FULLY INTEGRATED panelled dishwasher door that matches the EXACT SAME color, finish and gola profile as the rest of the cabinetry (no exposed metallic appliance front).\n"
                "  · 'Lavadora' / 'Lavadora 60' / washing machine: a DISTINCT, visible 60cm front-loading washing machine with round glass porthole door, placed in the EXACT base module drawn. It is NEVER a generic cabinet, drawer or panelled appliance.\n"
                "  · 'Secadora' / dryer: a DISTINCT, visible front-loading dryer with round glass porthole door, placed in the EXACT module drawn.\n"
                "  · 'BF-60' / 'Bajo Fregadero': sink base unit with undermount single sink basin and high-arc mixer tap.\n"
                "  · 'Bajo Placa 2 Gavetas' / '2 Gavetas': 90cm wide cooktop unit with TWO large closed horizontal pull-out drawers (gavetones) and black induction cooktop on the countertop.\n"
                "  · 'Gola Extraible 30' / 'Extraible': closed narrow 30cm pull-out bottle/spice base unit.\n"
                "- CAMERA FOR L-SHAPES: use a three-quarter view from inside or opposite the corner, so BOTH perpendicular walls and the 90-degree return are visibly distinct. A straight-on frontal elevation is forbidden for an L-shaped kitchen.\n"
                "- Use a wide-angle viewpoint so the COMPLETE layout is visible at once — from the "
                "corner if the layout turns, straight-on if it is a single straight wall. Whatever "
                "the angle, no module may end up outside the frame.\n\n"
                + (f"FINISHES (this is the ONLY thing the text decides — geometry comes 100% "
                   f"from the drawing): {brief_txt}\n\n" if brief_txt else
                   "Use plausible, restrained modern finishes; the geometry still comes 100% "
                   "from the drawing.\n\n")
                + "Masterpiece ultra-sharp 8K architectural interior photograph, pin-sharp tack focus across entire depth of field, maximum clarity and crisp definition on every edge, seam, joint and material texture. Extreme micro-detail PBR surfaces: razor-sharp wood grain, ultra-crisp marble veining, pristine reflections on glass and metal, clean gola channels. Balanced natural architectural daylight, realistic soft shadows, 16:9 aspect ratio. Zero blur, no noise, no smoothing artifacts, no cartoon or CGI plastic look. No text, dimension lines, watermarks, logos or people."
            )
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                reference_image_base64=ref_b64, reference_mime=ref_mime,
                provider=provider, reference_images=reference_images or None,
            )

        # ── SIN REFERENCIA = diseño desde cero ─────────────────────────────────
        # Expandir el brief con un LLM potente (gemini-2.5-pro) para que las órdenes
        # sean mucho más explícitas y el render obedezca con detalle.
        expanded_brief = await self._expand_brief(description, space_type)
        parsed_params["briefExpanded"] = bool(expanded_brief) and expanded_brief != (description or "").strip()

        # El brief expandido por el LLM puede "diluir" las órdenes literales por
        # módulo (p. ej. "el mueble de la izquierda lleva 1 cajón y 2 gavetas").
        # Antepone la descripción ORIGINAL como orden obligatoria y prioritaria,
        # para que el modelo de imagen respete los recuentos por módulo.
        raw_layout = (description or "").strip()
        combined = expanded_brief or description
        if raw_layout:
            combined = (
                "MANDATORY MODULE LAYOUT — obey this LITERALLY; it overrides anything else. "
                "Count the doors and drawers of EACH module exactly as written, left to right: "
                f"«{raw_layout}».\n\n" + (combined or "")
            )

        # Construir prompt GENÉRICO guiado por la descripción (ya expandida).
        prompt = self.build_render_prompt(
            description=combined,
            style=parsed_params.get("style", "photorealistic"),
            space_type=space_type,
        )

        # Crear tarea de generación de imagen (genérica, dirigida por el brief)
        # OJO: el caso del CROQUIS ya ha salido por su propia rama más arriba,
        # con prompt corto y sin brief expandido. Aquí solo llegan la referencia
        # que no es un dibujo y el diseño desde cero.
        if ref_b64:
            ref_note = (
                "An IMAGE has been attached as visual reference (a photo, a sketch or a "
                "technical breakdown/despiece). Work in PRECISE / STRUCTURE MODE: respect "
                "the real LAYOUT, PROPORTIONS and MEASUREMENTS of the piece (number and "
                "size of doors, drawers, shelves and columns) and the OPENINGS (windows "
                "and doors) at their original position and proportion. Keep the geometry "
                "faithful to the reference; apply only the finishes/colors from the brief. "
            )
        else:
            ref_note = ""
        task_prompt = (
            "Generate a single high-quality, photorealistic 3D render image based "
            "STRICTLY on the following design brief. Reproduce exactly what is "
            "described (type of furniture or space, exterior doors, finishes, "
            "colors, handles/pulls, materials and interior layout such as shelves, "
            "columns or drawers). Do NOT default to a kitchen unless the brief "
            "explicitly asks for one. "
            + ref_note
            + "\n\n"
            f"{prompt}\n\n"
            "The result must look like a real professional interior photograph "
            "(photorealistic, PBR materials, natural light, realistic shadows and "
            "reflections), NOT a cartoon or videogame-style 3D image. Avoid plastic, "
            "flat or oversaturated looks. No text, watermarks, or logos in the image."
        )

        return await self._render_dispatch(
            task_prompt, prompt, parsed_params,
            reference_image_base64=ref_b64, reference_mime=ref_mime,
            provider=provider,
        )

    async def generate_orbit_views(
        self,
        reference_image: str,
        reference_mime: Optional[str] = None,
        project_type: Optional[str] = None,
        n: int = 6,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Genera VARIAS vistas de la MISMA cocina/mueble desde distintos ángulos de
        cámara, a partir de un render base, para montar un visor orbital (girar con
        el ratón). Cada vista reutiliza la imagen base como referencia para mantener
        la coherencia (misma distribución, materiales, luz…); solo cambia la cámara.
        Devuelve las imágenes ordenadas de izquierda a derecha."""
        ref_b64, ref_mime = self._prepare_reference(reference_image, reference_mime)
        if not ref_b64:
            return {"success": False, "error": "Falta la imagen base del render."}

        pt = (project_type or "cocina").strip().lower()
        subject = {
            "armario": "wardrobe/closet", "bano": "bathroom", "cocina": "kitchen",
        }.get(pt, "kitchen/furniture")

        # Ángulos orbitales, de la esquina izquierda a la derecha (recorrido continuo).
        ANGLES = [
            "from the far LEFT corner of the room, camera rotated about 40 degrees to the left",
            "from the left, camera rotated about 20 degrees to the left",
            "a straight-on FRONTAL eye-level view, centered",
            "from the right, camera rotated about 20 degrees to the right",
            "from the far RIGHT corner of the room, camera rotated about 40 degrees to the right",
            "a slightly ELEVATED three-quarter view from the right corner",
        ]
        n = max(2, min(int(n or 6), len(ANGLES)))
        angles = ANGLES[:n]

        images = []
        for ang in angles:
            task_prompt = (
                f"You are given a reference image of an EXISTING {subject} design. "
                "Re-render the EXACT SAME scene — identical room, layout, modules, "
                "appliances, sink, hob, hood, colors, materials, finishes, floor, walls, "
                "windows and lighting — but seen from a DIFFERENT CAMERA ANGLE: "
                f"{ang}. Only the camera viewpoint changes, as if the viewer walked "
                "around the room; every object keeps its same identity, position and "
                "proportions relative to the room. Do NOT redesign, add, remove or move "
                "anything. Photorealistic result, PBR materials, natural light and "
                "realistic shadows, 16:9 landscape. No text, watermarks or logos."
            )
            try:
                res = await self._render_with_gemini(
                    task_prompt, task_prompt, {"space_type": subject, "orbitAngle": ang},
                    reference_image_base64=ref_b64, reference_mime=ref_mime,
                )
            except Exception as e:
                logger.error(f"orbit view error: {e}")
                res = None
            if res and res.get("success"):
                imgs = (res.get("result") or {}).get("images") or []
                if imgs:
                    images.append(imgs[0])

        return {
            "success": bool(images),
            "images": images,
            "count": len(images),
            "engine": self.config.brand_name,
        }

    # Tope de imágenes que se mandan juntas. No es un límite del modelo (admite
    # bastantes más): es un tope de criterio, porque cuantas más referencias se
    # mandan, menos atención recibe cada una y el render se vuelve un promedio.
    # Con 7 caben plano + 5 alzados + 1 referencia de acabado, o plano + 4
    # alzados + 2 referencias, que cubre una cocina en U con acabado de muestra.
    MAX_IMAGENES_COMPUESTAS = 7

    async def generate_render_composed(
        self,
        description: str,
        floor_plan: Optional[str] = None,
        wall_sketches: Optional[list] = None,
        params_override: Optional[Dict[str, Any]] = None,
        reference_images: Optional[list] = None,
        provider: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Genera UN render fotorrealista combinando un PLANO EN PLANTA (distribución)
        y un BOCETO por cada PARED (diseño de esa pared), fiel a ambos.

        Args:
            description: brief del acabado deseado (colores, materiales, estilo…)
            floor_plan: plano en planta (base64/dataURL/PDF)
            wall_sketches: lista de bocetos, uno por pared (base64/dataURL)
            params_override: overrides (p.ej. style)
        """
        parsed_params = self.parse_natural_language(description or "")
        if params_override:
            parsed_params.update(params_override)
        # El TIPO lo dice la pantalla (cocina/armario/baño); solo si no viene se
        # adivina del texto. Adivinarlo teniendo el dato es perder informacion.
        space_type = self.detect_space_type(project_type or description or "cocina")
        parsed_params["space_type"] = space_type

        images = []       # [{"data","mime"}] para la generación multi-imagen
        ref_lines = []    # descripción textual de cada imagen para el prompt
        hay_croquis = False  # ¿alguna de las que manda la geometría va a mano?

        dpi_referencia = 280 if provider == "julio11_plus" else 150
        if floor_plan:
            b64, mime = self._prepare_reference(
                floor_plan, None, pdf_dpi=dpi_referencia)
            if b64:
                images.append({"data": b64, "mime": mime})
                ref_lines.append(
                    f"- IMAGE {len(images)} is the FLOOR PLAN (top-down view): it defines the "
                    "exact LAYOUT — position and length of every wall, placement of cabinets/"
                    "furniture, doors and windows. Respect these positions and proportions."
                )
                hay_croquis = hay_croquis or self._parece_dibujo_a_mano(b64)

        for i, sk in enumerate(wall_sketches or []):
            if len(images) >= self.MAX_IMAGENES_COMPUESTAS:
                break
            b64, mime = self._prepare_reference(
                sk, None, pdf_dpi=dpi_referencia)
            if b64:
                images.append({"data": b64, "mime": mime})
                ref_lines.append(
                    f"- IMAGE {len(images)} is a reference (render/photo/sketch) of WALL {i + 1}: "
                    "it shows the exact design of that wall (cabinets, shelves, appliances, "
                    "finishes, proportions). Reproduce that wall faithfully, as shown."
                )
                hay_croquis = hay_croquis or self._parece_dibujo_a_mano(b64)

        # Referencias de ACABADO: la foto que trae el cliente ("quiero esta
        # madera, este tirador"). Se pueden usar A LA VEZ que el plano: el plano
        # manda en la distribución y la referencia manda en el acabado. Sin
        # esto, elegir plano significaba renunciar a la referencia.
        for ref in (reference_images or []):
            if len(images) >= self.MAX_IMAGENES_COMPUESTAS:
                break
            b64, mime = self._prepare_reference(
                ref, None, pdf_dpi=dpi_referencia)
            if b64:
                images.append({"data": b64, "mime": mime})
                ref_lines.append(
                    f"- IMAGE {len(images)} is a FINISH/STYLE reference: take from it ONLY the "
                    "materials, colours, textures, handle system and general character. Do NOT "
                    "take its layout, its cabinet sizes or its room: the layout comes from the "
                    "floor plan and the wall references above."
                )

        if not images:
            return {
                "success": False,
                "status": "failed",
                "error": "Adjunta al menos el plano en planta o un boceto de pared.",
                "engine": self.config.brand_name,
            }

        # IA7 compuesta: base sencilla de julio, sin OCR ni lectura estructurada,
        # más la regla estricta de geometría y vanos del 22/07.
        if provider == "julio11_plus":
            brief_txt = (description or "").strip()
            refs_block = "\n".join(ref_lines)
            task_prompt = (
                "You are given technical drawings of ONE specific project. Recreate THAT SAME "
                "project as a single photorealistic interior photograph. The drawings are the "
                "ground truth for GEOMETRY, not decoration.\n"
                + refs_block + "\n\nSTRICT STRUCTURE / PRECISE MODE:\n"
                "- Preserve the EXACT shape, wall runs, corners, number and left-to-right order "
                "of modules, appliances and tall columns.\n"
                "- Preserve every window and door at the SAME position, width and height.\n"
                "- Keep module widths and overall proportions to scale. Do not add, remove, resize, "
                "merge, duplicate or rearrange any module or opening.\n"
                + (f"- Take ONLY finishes, materials and colours from this written brief: {brief_txt}\n"
                   if brief_txt else
                   "- Keep the finishes, materials and colours shown in the references.\n")
                + "- Geometry comes 100% from the drawings. Produce a clean photorealistic image "
                "without text, dimensions, arrows, labels, watermarks or logos."
            )
            parsed_params["motor"] = "IA 7 — IA0 con lectura mejorada"
            parsed_params["hasReference"] = True
            parsed_params["referenceCount"] = len(images)
            return await self._render_dispatch(
                task_prompt, task_prompt, parsed_params,
                provider="julio11_plus", reference_images=images,
            )

        # Si la referencia incluye croquis a mano, ejecutar transcripción Vision OCR preliminar
        sketch_transcription_block = ""
        if hay_croquis:
            transcriptions = []
            for img_info in images:
                if self._parece_dibujo_a_mano(img_info["data"]):
                    t_txt = await self._transcribe_sketch_with_vision(img_info["data"], img_info.get("mime", "image/png"))
                    if t_txt:
                        transcriptions.append(t_txt)
            if transcriptions:
                sketch_transcription_block = (
                    "\n\nEXACT TECHNICAL OCR BREAKDOWN READ FROM THE HANDWRITTEN SKETCH (MANDATORY):\n"
                    + "\n---\n".join(transcriptions) + "\n\n"
                    "CRITICAL MANDATORY RULES FROM SKETCH OCR:\n"
                    "- IF OCR SPECIFIES 2 TALL COLUMNS SIDE-BY-SIDE (e.g. 1x Refrigerator 60cm + 1x Freezer 60cm), RENDER EXACTLY 2 FULL-HEIGHT TALL COLUMNS SIDE-BY-SIDE ON THAT WALL END. DO NOT MERGE THEM INTO ONE COLUMN!\n"
                    "- IF HANDWRITTEN TEXT WRITTEN ON PAPER SPECIFIES FINISHES (e.g. 'Blanco Mate', 'granito Nacional'), RENDER DOORS IN MATTE WHITE AND COUNTERTOP IN NATIONAL GRANITE.\n"
                    "- KEEP EXACT SEQUENCE OF OVEN, DRAWERS, SINK AND EXTRAÍBLE AS EXTRACTED ABOVE.\n"
                    "- REPRODUCE THE FRONTS OF EACH MODULE EXACTLY AS LISTED ABOVE: the same number of fronts and the same kind. "
                    "A module listed with 3 drawers is rendered with 3 separate drawer fronts, never as one plain door; "
                    "a tall column listed with 2 doors is rendered split in two, never as a single full-height door.\n"
                    "- ANY GAP OR RECESS REPORTED IN THE WALL-UNIT RUN (typically above the hob, for the hood) MUST STAY OPEN. "
                    "Do not fill it with an invented cabinet and do not widen the neighbouring units to close it.\n"
                    "- RENDER BOTH ENDS OF THE RUN, INCLUDING THE LAST MODULE ON THE RIGHT, AND FRAME THE SHOT WIDE ENOUGH THAT "
                    "NO MODULE IS CROPPED AT THE EDGE OF THE IMAGE.\n"
                )

        brief_txt = (description or "").strip()
        refs_block = "\n".join(ref_lines)
        task_prompt = (
            "You are given reference images of ONE specific kitchen. Recreate THAT SAME kitchen "
            "as a single photorealistic interior photograph. This is a FAITHFUL re-render of the "
            "references, NOT a new design — copy what the images show.\n"
            + refs_block + "\n"
            + sketch_transcription_block
            # Si lo que manda la geometría es un DIBUJO A MANO, hay que decirlo.
            + ("\nIMPORTANT: the drawing(s) above are HAND-DRAWN by the designer (pencil or pen "
               "on paper, possibly with handwritten dimensions). They are a TECHNICAL SPECIFICATION, "
               "not a style reference. Read the geometry from them and build it exactly: do NOT "
               "reproduce the paper, the pencil strokes or the handwriting in the final image, and "
               "do NOT 'tidy up', simplify or upgrade the layout because it looks rough — a "
               "hand-drawn L-shaped kitchen must come out as that same L-shaped kitchen, with two "
               "perpendicular cabinet runs visibly joined at the actual inside corner.\n"
               if hay_croquis else "")
            # UNA FOTO NO LLEVA COTAS. NUNCA. (24/08/2026)
            #
            # El master: «si paso un diseño con medidas escritas, cuando lo pasa
            # a render las escribe». Y era verdad: lo único que impedía copiar
            # las anotaciones del dibujo era la regla de más arriba, la de «no
            # reproduzcas el papel ni la letra manuscrita»… que SOLO se añade si
            # `_parece_dibujo_a_mano` dice que sí. Un plano impreso de CAD —o el
            # pantallazo de un presupuesto— no lo es, así que esa regla no se
            # ponía y nadie le decía al modelo que no copiase las cotas.
            #
            # Va SIN condición y aparte de la de la letra, porque son dos cosas
            # distintas: aquella habla del soporte (papel, lápiz), ésta habla de
            # las ANOTACIONES TÉCNICAS, que aparecen igual en un dibujo impreso.
            #
            # Y es la regla de la casa: un modelo de imagen NUNCA escribe cotas
            # —no sabe— así que las que saliesen serían números inventados sobre
            # una foto que alguien puede acabar usando para fabricar. Las cotas
            # de verdad las dibuja el alzado vectorial, con datos reales.
            + "\nTHIS IS A PHOTOGRAPH, NOT A PLAN:\n"
            "- NEVER draw dimension lines, arrows, extension lines, leaders, measurement "
            "numbers, unit marks (mm/cm), module codes, labels, callouts, legends, title "
            "blocks, watermarks or ANY text or annotation on the image. The reference "
            "drawings may be covered in written dimensions: those are INSTRUCTIONS FOR YOU "
            "about how big things are, never something to copy onto the photograph.\n"
            "- The result must look like a photograph taken with a camera in a finished "
            "room: real materials, real light, and not one single number or letter "
            "printed anywhere on it.\n"
            + "\nSTRICT RULES:\n"
            "- Show the WHOLE kitchen: include EVERY wall, every cabinet run and EVERY element "
            "that appears in ANY of the reference images. Do NOT omit, crop out or leave out any "
            "part of the kitchen (e.g. the tall fridge/oven columns, an end run or the island). "
            "For an L-shaped layout, render two clearly perpendicular runs joined at the inside corner; "
            "the return wall must visibly recede in depth and must never be flattened into a frontal wall. "
            "Use a three-quarter wide-angle corner view so the complete L/U/peninsula layout is visible at once.\n"
            "- Keep the EXACT same layout and the SAME cabinet modules (number, order, widths and "
            "heights), the same wall units, base units, tall/column units, the same appliances "
            "(fridge, oven, microwave, hob, hood, dishwasher), sink, windows, doors and "
            "island/peninsula, each in the SAME position and proportion as in the reference images.\n"
            "- Do NOT add, remove, move, merge, duplicate or restyle anything that is not "
            "explicitly requested below. Reproduce the SAME number of doors/drawers and the same "
            "appliance positions; nothing from the references may be missing.\n"
            + (f"- Apply ONLY these finishes/changes, keep everything else identical to the references: {brief_txt}\n"
               if brief_txt else
               "- Keep the same finishes, colors and materials shown in the references.\n")
            + "- Masterpiece ultra-sharp 8K architectural interior photograph, pin-sharp tack focus across entire depth of field, maximum clarity on every line, joint, edge and seam. Extreme micro-detail PBR materials: razor-sharp wood grain, ultra-crisp marble veining, pristine reflections on glass and metal, clean gola channels. Balanced natural daylight, soft realistic shadows, 16:9. Zero blur, no compression noise, no plastic or CGI look. No text, watermarks, logos, people or invented extra objects."
        )
        prompt = task_prompt
        parsed_params["hasReference"] = True
        parsed_params["referenceCount"] = len(images)
        return await self._render_dispatch(
            task_prompt, prompt, parsed_params,
            provider=provider, reference_images=images,
        )

    # Dos casos reales, y cada uno necesita su umbral:
    #  · Croquis a LÁPIZ: casi sin color. Basta con exigir poca saturación.
    #  · Croquis a BOLÍGRAFO rojo/azul: el trazo sí tiene color, pero es un trazo
    #    fino: el papel sigue ocupando casi toda la imagen.
    # Lo que NO vale es medir el BRILLO medio: una foto de una cocina blanca da
    # 0,85 y un croquis 0,97 — con el listón en 0,30 pasaban las dos, y una foto
    # de la cocina del cliente tomada por croquis se rediseña entera en vez de
    # editarse. Lo que separa el papel de una foto es cuánta imagen es papel.
    CROQUIS_SATURACION_MAX = 0.10       # lápiz/grafito: casi sin color
    CROQUIS_SATURACION_TINTA_MAX = 0.35  # bolígrafo rojo/azul
    CROQUIS_FONDO_CLARO_MIN = 0.55      # fracción de píxeles casi blancos (papel)
    CROQUIS_FONDO_CLARO_TINTA_MIN = 0.80  # con tinta de color se exige más papel

    def _parece_dibujo_a_mano(self, raw_b64):
        """¿Este mapa de bits es un croquis/plano a mano y no la FOTO de una
        cocina real? Papel + trazo = casi sin color y con mucho fondo claro.

        CONSERVADOR a propósito: ante la duda devuelve False y la imagen se
        sigue tratando como foto, que es el comportamiento de siempre.
        Confundir una foto con un croquis también estropea el render."""
        try:
            import base64
            import io
            from PIL import Image, ImageChops, ImageStat
            raw = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
            img = Image.open(io.BytesIO(base64.b64decode(raw))).convert("RGB")
            img.thumbnail((160, 160))
            # Saturación media: en HSV de PIL es (max-min)/max, justo lo que
            # separa un trazo de lápiz (gris) de una cocina real (con color).
            saturacion = ImageStat.Stat(img.convert("HSV").split()[1]).mean[0] / 255.0
            # Fracción de píxeles casi blancos = el papel. Se mira el canal MÁS
            # OSCURO de cada píxel: blanco de verdad es alto en R, G y B a la vez.
            r, g, b = img.split()
            minimo = ImageChops.darker(ImageChops.darker(r, g), b)
            fondo_claro = ImageStat.Stat(
                minimo.point(lambda v: 255 if v >= 200 else 0)).mean[0] / 255.0
            if (saturacion <= self.CROQUIS_SATURACION_MAX
                    and fondo_claro >= self.CROQUIS_FONDO_CLARO_MIN):
                return True
            # Trazo de color: se admite más saturación, pero el papel tiene que
            # mandar de forma clara. Una foto de cocina no llega a este fondo.
            return (saturacion <= self.CROQUIS_SATURACION_TINTA_MAX
                    and fondo_claro >= self.CROQUIS_FONDO_CLARO_TINTA_MIN)
        except Exception as e:
            logger.debug(f"No se pudo analizar la referencia como croquis: {e}")
            return False

    async def _render_croquis_de_armario(self, *, ref_b64, ref_mime, brief_txt,
                                         parsed_params, provider, reference_images,
                                         prompt_croquis_armario):
        """Realiza EN FOTO el armario dibujado, con reglas de armario.

        Mismo esqueleto que el camino de cocina —recortar el dibujo de la
        página, leerlo a ficha, encargar la foto— pero preguntando lo que tiene
        un armario: cuerpos, altillo corrido, barra, baldas, cajonera. Ver
        `render_armario.py` para por qué esto no podía seguir compartiendo el
        encargo de cocina.
        """
        parsed_params["pieza"] = "armario"

        # EL DIBUJO, A PANTALLA COMPLETA. El master dibuja con el dedo en una app
        # que ocupa la pantalla entera de barras de herramientas y paletas de
        # color: el armario es un tercio de la imagen. Recorta solo cuando lo
        # tiene claro; ante la duda devuelve la original.
        try:
            from services.recorte_croquis import recortar_dibujo_base64
            recortado, hubo_recorte = recortar_dibujo_base64(ref_b64, ref_mime)
            if hubo_recorte:
                ref_b64, ref_mime = recortado, "image/png"
                parsed_params["dibujoRecortado"] = True
                logger.info("Croquis de armario recortado de la página.")
        except Exception as e:
            logger.warning(f"No se pudo recortar el croquis de armario: {e}")

        # LO QUE ÉL ESCRIBIÓ VA A LA LECTURA, NO SOLO A LOS ACABADOS. Ver
        # `lectura_armario.prompt_lectura`: su descripción daba los cuerpos, los
        # cajones y qué lado es más ancho, y se archivaba bajo «FINISHES».
        lectura = await self._leer_armario_del_dibujo(ref_b64, ref_mime, brief_txt)
        if lectura:
            from services.luiggi_ai.lectura_armario import (
                especificacion_en_texto, resumen_para_pantalla)
            transcripcion = especificacion_en_texto(lectura)
            parsed_params["lecturaDelDibujo"] = resumen_para_pantalla(lectura)
            parsed_params["lecturaEstructurada"] = True
        else:
            # QUE SE CAIGA AL MÉTODO VIEJO NO PUEDE SER INVISIBLE. Sin ficha no
            # hay recuento de cuerpos, y sin recuento el render vuelve a poder
            # inventarse módulos. Que se vea en pantalla.
            transcripcion = ""
            parsed_params["lecturaEstructurada"] = False
            parsed_params["lecturaDelDibujo"] = (
                "No se ha podido leer el armario a ficha (cuerpos y medidas uno a uno). "
                "El render puede perder la cuenta de cuerpos. Vuelve a intentarlo, o sube "
                "el dibujo más grande y recortado."
            )

        task_prompt = prompt_croquis_armario(transcripcion=transcripcion, brief=brief_txt)
        return await self._render_dispatch(
            task_prompt, task_prompt, parsed_params,
            reference_image_base64=ref_b64, reference_mime=ref_mime,
            provider=provider, reference_images=reference_images or None,
        )

    async def _leer_armario_del_dibujo(self, raw_b64: str, mime: str = "image/png",
                                       brief: str = ""):
        """Lee el croquis de un armario A FICHA: cuerpos, altillo e interior.

        Devuelve el diccionario ya limpio, o None si no hay lectura fiable.
        Nunca lanza: esto va en medio de un render que el master está mirando.
        """
        try:
            from services.llm_vision import analyze_image_with_gemini
            from services.luiggi_ai.lectura_armario import prompt_lectura, parsear_lectura
            crudo = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
            res = await analyze_image_with_gemini(
                crudo, prompt_lectura(brief), model="gemini-2.5-flash",
                image_mime=mime or "image/jpeg")
            lectura = parsear_lectura(res or "")
            if lectura:
                logger.info("Armario leído a ficha: %s cuerpo(s), altillo=%s.",
                            len(lectura.get("cuerpos") or []),
                            bool((lectura.get("altillo") or {}).get("hay")))
            else:
                logger.warning("La lectura del armario no se pudo interpretar.")
            return lectura
        except Exception as e:
            logger.warning(f"Error leyendo el armario del dibujo: {e}")
            return None

    async def _leer_cocina_del_dibujo(self, raw_b64: str, mime: str = "image/png"):
        """Lee el dibujo A FICHA: lista de muebles con fila, ancho y frentes.

        Devuelve el diccionario ya limpio, o None si no hay lectura fiable —y
        entonces quien llama se queda con la transcripción en prosa de siempre,
        que es peor pero es algo. Nunca lanza: esto va en medio de un render
        que el master está mirando.
        """
        try:
            from services.llm_vision import analyze_image_with_gemini
            from services.luiggi_ai.lectura_cocina import PROMPT_LECTURA, parsear_lectura
            crudo = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
            res = await analyze_image_with_gemini(
                crudo, PROMPT_LECTURA, model="gemini-2.5-flash",
                image_mime=mime or "image/jpeg")
            lectura = parsear_lectura(res or "")
            if lectura:
                filas = lectura.get("filas") or {}
                logger.info(
                    "Dibujo leído a ficha: %s bajos, %s altos, %s altillos, %s columnas, %s hueco(s).",
                    len(filas.get("bajos") or []), len(filas.get("altos") or []),
                    len(filas.get("altillos") or []), len(filas.get("columnas") or []),
                    len(lectura.get("huecos_altos") or []))
            else:
                logger.warning("La lectura a ficha no se pudo interpretar; se usa la de siempre.")
            return lectura
        except Exception as e:
            logger.warning(f"Error leyendo la cocina del dibujo: {e}")
            return None

    async def _transcribe_sketch_with_vision(self, raw_b64: str, mime: str = "image/png") -> str:
        """Lee el croquis manuscrito con Gemini Vision y extrae de forma
        estructurada los módulos, cotas, frigorífico, hornos, columnas y acabados manuscritos.

        LO QUE NO SE TRANSCRIBE, NO SE RENDERIZA. Este texto se antepone tal cual
        al encargo del render, así que todo lo que aquí no se pregunte se pierde
        para siempre: el modelo de imagen ya no vuelve a mirar el dibujo con
        atención, mira este resumen. Por eso se piden explícitamente los FRENTES
        de cada módulo (un mueble con tres cajones dibujados es tres cajones, no
        una puerta), los HUECOS de la fila de altos (el de la campana sobre la
        placa se rellenaba con un mueble inventado) y el ÚLTIMO MÓDULO DE CADA
        EXTREMO (el de la derecha del todo desaparecía del render).
        """
        try:
            from services.llm_vision import analyze_image_with_gemini
            prompt = (
                "Analyze this hand-drawn technical kitchen blueprint / elevation drawing with extreme precision.\n"
                "Read every handwritten label, dimension number, and finish text written on the paper.\n"
                "Extract the EXACT specification in English:\n"
                "1. FINISHES & MATERIALS: read any handwritten text written on paper (e.g. 'Blanco Mate' -> Matte white doors/fronts, 'encimera granito Nacional' -> National granite countertop, 'Luxe', 'Zenit').\n"
                "2. TALL COLUMNS COUNT AND TYPES: Count how many full-height tall columns are drawn side-by-side (e.g. '2 SEPARATE TALL COLUMNS: 1x Refrigerator column 60cm + 1x Freezer/Congelador column 60cm'). Explicitly state if there are 2 separate tall columns or 1 single column. DO NOT MERGE multiple tall columns into one!\n"
                "3. BASE CABINET SEQUENCE (left to right / around walls): list each module with label (e.g. 'Horno', '2 gavetas', 'Ex/Extraíble', 'Fregadero', 'Frigo', 'Congelador') and width in cm/mm.\n"
                "4. WALL CABINETS & HOOD: describe upper cabinets, open shelves, and wall hood placement. State explicitly "
                "whether the upper band is ONE row of wall units or TWO STACKED ROWS (wall units with a second row of shorter "
                "units — altillos — on top, usually up to the ceiling), and whether they reach the ceiling or stop short.\n"
                "5. CORNER & LAYOUT SHAPE: L-shaped, U-shaped, or linear, including corner module dimensions (e.g. 93x93 cm). If the drawing visibly turns at an inside corner or shows a secondary wall/return, classify it as L-shaped even when one wall is drawn mostly frontally. State the MAIN WALL sequence and the RETURN WALL sequence separately.\n"
                "6. FRONTS OF EACH MODULE (one line per module, this is MANDATORY and must never be summarised away): "
                "for EVERY module of every run — base units, wall units and tall columns — state HOW MANY separate fronts it has "
                "and WHAT KIND each one is, reading the horizontal and vertical dividing lines drawn on its face. "
                "Use exactly this form: 'module 3, 60cm, sink base: 1 door' / 'module 4, 90cm: 3 stacked drawers' / "
                "'tall column 1, 60cm: 2 doors, one above the other, split at oven height'. "
                "A horizontal line across the face of a unit means the face is split into that many stacked fronts (drawers or two doors). "
                "A vertical line down the middle means two side-by-side doors. "
                "Count them one by one and NEVER merge several drawn fronts into a single panel.\n"
                "7. GAPS AND RECESSES IN THE WALL-UNIT RUN: state whether the row of wall cabinets is continuous or is INTERRUPTED, "
                "and where. A gap above the hob (normally for the extractor hood), a shorter wall unit, an open shelf or a bare stretch of wall "
                "is a REAL part of the design and must be reported as such: e.g. 'wall run: 2 units, then a 90cm gap above the hob occupied only by the hood, then 1 unit'. "
                "If the wall run is truly continuous with no interruption, say so explicitly.\n"
                "8. THE TWO ENDS OF THE RUN: describe separately what is drawn at the FAR LEFT end and at the FAR RIGHT end of the drawing "
                "— the last module of each side, its width and what it is (cabinet, tall column, appliance, open shelving, end panel, or bare wall). "
                "Never leave an end undescribed: if a module is drawn at the very edge of the paper, it is part of the kitchen and must be listed.\n"
                "9. RELATIVE HEIGHTS: state which blocks are FULL-HEIGHT columns (drawn from the floor line up to or "
                "above the top of the wall cabinets) and which are wall units or base units. Say explicitly whether the "
                "columns rise ABOVE the line of the wall cabinets. A block drawn floor-to-top in one piece is ONE tall "
                "column, not a base unit with a wall unit above it.\n"
                "10. IS THIS THE WHOLE PAGE? The image may be a phone screenshot of a document: a title, a brand box, "
                "priced line items, totals and the phone's status/navigation bars around the actual drawing. Ignore all "
                "of it and describe ONLY the drawing — except the stated SHAPE of the job if it appears in the title "
                "('Cocina lineal' = straight single-wall run, 'en L', 'en U'), which you should report as the layout.\n"
                "Be strictly factual, clear, and concise."
            )
            raw = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
            res = await analyze_image_with_gemini(raw, prompt, model="gemini-2.5-flash", image_mime=mime or "image/jpeg")
            return res.strip() if res else ""
        except Exception as e:
            logger.warning(f"Error transcribiendo croquis con Vision: {e}")
            return ""

    def _is_sketch_reference(self, reference_image, reference_mime):
        """Detecta si la referencia es un croquis/plano manuscrito (PDF escaneado
        O FOTO/ESCANEO de un dibujo a mano) en vez de una foto de cocina existente."""
        if not reference_image:
            return False
        if reference_mime and "pdf" in reference_mime.lower():
            return True
        if reference_image[:60].lower().startswith("data:application/pdf"):
            return True
        raw = reference_image.split(",", 1)[-1] if "," in reference_image else reference_image
        try:
            import base64
            header_bytes = base64.b64decode(raw[:20])
            if header_bytes[:4] == b"%PDF":
                return True
        except Exception:
            pass
        return self._parece_dibujo_a_mano(raw)

    def _prepare_reference(self, reference_image, reference_mime, pdf_dpi: int = 150):
        """Normaliza la referencia y rasteriza la primera página del PDF.

        El perfil estable conserva 150 dpi. El perfil experimental puede pedir
        más detalle sin modificar el comportamiento de IA0.
        """
        if not reference_image:
            return None, "image/png"
        try:
            raw = reference_image
            mime = reference_mime or "image/png"
            if raw.startswith("data:"):
                header, raw = raw.split(",", 1)
                if "pdf" in header.lower():
                    mime = "application/pdf"
                elif "png" in header.lower():
                    mime = "image/png"
                elif "webp" in header.lower():
                    mime = "image/webp"
                elif "jpeg" in header.lower() or "jpg" in header.lower():
                    mime = "image/jpeg"
            from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
            if mime == "application/pdf" or is_pdf_base64(raw):
                pages = pdf_base64_to_png_base64(
                    raw, dpi=max(150, min(int(pdf_dpi or 150), 300)), max_pages=1) or []
                if pages:
                    p = pages[0]
                    if p.startswith("data:"):
                        p = p.split(",", 1)[1]
                    return p, "image/png"
                return None, "image/png"
            return raw, mime
        except Exception as e:
            logger.warning(f"Referencia de render ignorada: {e}")
            return None, "image/png"

    async def generate_render_from_params(
        self,
        layout: str = "L-shape",
        countertop: str = "quartz_white",
        cabinets: str = "white_matte",
        handles: str = "bar_black",
        floor: str = "wood_oak",
        lighting: str = "natural",
        style: str = "photorealistic",
        additional_details: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Genera un render 3D a partir de parámetros explícitos (formulario).
        """
        prompt = self.build_kitchen_prompt(
            layout=layout,
            countertop=countertop,
            cabinets=cabinets,
            handles=handles,
            floor=floor,
            lighting=lighting,
            style=style,
            additional_details=additional_details,
        )

        task_prompt = (
            f"Generate a single ultra-photorealistic interior photograph (NOT a cartoon "
            f"or videogame-style 3D image):\n\n{prompt}\n\n"
            f"Output: one realistic photo with PBR materials, natural light and realistic "
            f"shadows/reflections. Avoid plastic, flat or oversaturated looks."
        )

        return await self._render_dispatch(task_prompt, prompt)

    async def _render_with_gemini(self, task_prompt: str, prompt: str,
                                  parsed_params: Optional[Dict[str, Any]] = None,
                                  reference_image_base64: Optional[str] = None,
                                  reference_mime: str = "image/png",
                                  reference_images: Optional[list] = None,
                                  model_override: Optional[str] = None,
                                  prompt_prefix: Optional[str] = None) -> Dict[str, Any]:
        """Genera el render con Gemini y lo devuelve como data URL (marca blanca)."""
        from services.llm_vision import generate_image_with_gemini
        start = time.time()
        # Aplicar prefijo de prompt si se especifica (IA 3 premium)
        final_prompt = f"{prompt_prefix}\n\n{task_prompt}" if prompt_prefix else task_prompt
        _info_modelo = {}
        try:
            data_url = await generate_image_with_gemini(
                final_prompt,
                reference_image_base64=reference_image_base64,
                reference_mime=reference_mime or "image/png",
                reference_images=reference_images,
                model_override=model_override,
                salida=_info_modelo,
            )
        except Exception as e:
            logger.error(f"Render (Gemini) error: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": "No se pudo generar el render. Inténtalo de nuevo.",
                "engine": self.config.brand_name,
            }
        out = {
            "success": True,
            "status": "completed",
            "result": {"images": [data_url]},
            "engine": self.config.brand_name,
            "duration_seconds": round(time.time() - start, 1),
            "prompt_used": prompt,
        }
        if parsed_params is not None:
            # El modelo que ha pintado la imagen viaja con el render. Sin esto,
            # un motor que falla y cae al de respaldo devuelve una imagen que
            # parece la buena, y comparar dos motores deja de tener sentido.
            # POR NOMBRE DE CASA, NO POR EL DEL MODELO. Qué motor hay detrás
            # es secreto industrial y el Estudio 3D lo ve cualquier carpintero
            # con cuenta: el nombre técnico se queda en el log y en Ajustes →
            # Consumo de IA, que está cerrado a master. Aquí sube una etiqueta,
            # que es lo único que hace falta para comparar dos renders.
            if _info_modelo.get("modelo"):
                parsed_params["motorUsado"] = _etiqueta_de_motor(_info_modelo["modelo"])
                if _info_modelo.get("de_respaldo"):
                    parsed_params["motorDeRespaldo"] = _etiqueta_de_motor(
                        _info_modelo.get("modelo_pedido") or "")
            out["parsed_params"] = parsed_params
        return out

    async def _render_with_flux(self, task_prompt: str, prompt: str,
                                 parsed_params: Optional[Dict[str, Any]] = None,
                                 reference_image_base64: Optional[str] = None,
                                 reference_mime: str = "image/png",
                                 replicate_key: str = "") -> Dict[str, Any]:
        """Genera el render con Flux Pro (black-forest-labs/flux-1.1-pro) via Replicate.
        Devuelve la imagen como data URL base64 para consistencia con los otros motores.
        Requiere REPLICATE_API_TOKEN en el entorno."""
        import asyncio
        import base64
        import httpx
        start = time.time()
        try:
            # Preparar input para Flux 1.1 Pro
            flux_input: Dict[str, Any] = {
                "prompt": f"{_PREMIUM_PROMPT_PREFIX}\n\n{task_prompt}",
                "aspect_ratio": "16:9",
                "output_format": "png",
                "output_quality": 95,
                "safety_tolerance": 5,
                "prompt_upsampling": True,
            }
            # Si hay imagen de referencia, usarla como img2img (Flux Redux)
            # Flux 1.1 Pro no acepta img2img directamente; usamos solo el prompt
            # (en el futuro se puede usar flux-redux para img2img)

            headers = {
                "Authorization": f"Bearer {replicate_key}",
                "Content-Type": "application/json",
                "Prefer": "wait",  # esperar resultado directamente (hasta 60s)
            }

            async def _call_replicate():
                async with httpx.AsyncClient(timeout=120) as client:
                    # Crear predicción
                    resp = await client.post(
                        # flux-1.1-pro, NO flux-schnell. Schnell genera en 4 pasos de difusion
                        # frente a los ~25-50 del Pro: sale mas barato (~0,003 $/img)
                        # pero la calidad no es la que el master eligio para IA 3.
                        # Se cambio a Schnell por coste el 01/08 y se revirtio el 06/08.
                        "https://api.replicate.com/v1/models/black-forest-labs/flux-1.1-pro/predictions",
                        headers=headers,
                        json={"input": flux_input},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    # Con Prefer: wait, el resultado puede venir directo
                    if data.get("status") == "succeeded" and data.get("output"):
                        return data["output"]
                    # Si no, hacer polling
                    prediction_url = data.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{data['id']}"
                    for _ in range(60):  # hasta 120s
                        await asyncio.sleep(2)
                        poll = await client.get(prediction_url, headers=headers)
                        poll.raise_for_status()
                        pd = poll.json()
                        if pd.get("status") == "succeeded":
                            return pd.get("output")
                        if pd.get("status") in ("failed", "canceled"):
                            raise RuntimeError(f"Flux falló: {pd.get('error', 'unknown')}")
                    raise RuntimeError("Flux: tiempo de espera agotado")

            output = await _call_replicate()
            # output es una URL o lista de URLs con la imagen generada
            image_url = output[0] if isinstance(output, list) else output
            if not image_url:
                raise RuntimeError("Flux no devolvio imagen")

            # Descargar la imagen y convertir a data URL
            async with httpx.AsyncClient(timeout=60) as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                img_b64 = base64.b64encode(img_resp.content).decode("ascii")
                data_url = f"data:image/png;base64,{img_b64}"

            out = {
                "success": True,
                "status": "completed",
                "result": {"images": [data_url]},
                "engine": f"{self.config.brand_name} (Flux Pro)",
                "duration_seconds": round(time.time() - start, 1),
                "prompt_used": prompt,
            }
            if parsed_params is not None:
                out["parsed_params"] = parsed_params
            return out

        except Exception as e:
            logger.error(f"Render (Flux) error: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": f"Flux Pro no pudo generar el render: {str(e)[:200]}",
                "engine": self.config.brand_name,
            }

    async def _render_with_manus(self, task_prompt: str, prompt: str,
                                 parsed_params: Optional[Dict[str, Any]] = None,
                                 reference_image_base64: Optional[str] = None,
                                 reference_mime: str = "image/png") -> Dict[str, Any]:
        """Genera el render usando el motor Manus (LuiggiAICore): crea una tarea,
        espera a que termine y devuelve la(s) imagen(es) ya servidas por el proxy
        white-label. Las URLs vienen como rutas internas /api/ai-engine/asset."""
        from .engine_core import get_engine
        engine = get_engine()
        start = time.time()
        try:
            files = None
            if reference_image_base64:
                try:
                    import base64 as _b64
                    raw = _b64.b64decode(reference_image_base64)
                    ext = "png" if "png" in (reference_mime or "") else "jpg"
                    up = await engine.upload_file(raw, f"reference.{ext}")
                    if up.get("success") and up.get("file_id"):
                        files = [{"file_id": up["file_id"]}]
                except Exception as e:
                    logger.warning(f"Manus: no se pudo subir la referencia: {e}")

            created = await engine.create_task(prompt=task_prompt, files=files)
            if not created.get("success"):
                return {
                    "success": False, "status": "failed",
                    "error": created.get("error", "No se pudo iniciar el render."),
                    "engine": self.config.brand_name,
                }
            task_id = created.get("task_id")
            done = await engine.wait_for_completion(task_id, timeout=300, poll_interval=5)
            if not done.get("success"):
                return {
                    "success": False, "status": done.get("status", "failed"),
                    "error": done.get("error", "El render no se completó."),
                    "engine": self.config.brand_name,
                }
            # Las imágenes (proxy URLs) están en result.images (o anidado)
            msgs = done.get("result", {}) or {}
            images = msgs.get("images") or []
            if not images and isinstance(msgs.get("result"), dict):
                images = msgs["result"].get("images") or []
            if not images:
                return {
                    "success": False, "status": "failed",
                    "error": "El motor no devolvió ninguna imagen.",
                    "engine": self.config.brand_name,
                }
            out = {
                "success": True, "status": "completed",
                "result": {"images": images},
                "engine": self.config.brand_name,
                "duration_seconds": round(time.time() - start, 1),
                "prompt_used": prompt,
            }
            if parsed_params is not None:
                out["parsed_params"] = parsed_params
            return out
        except Exception as e:
            logger.error(f"Render (Manus) error: {e}")
            return {
                "success": False, "status": "failed",
                "error": "No se pudo generar el render con el motor.",
                "engine": self.config.brand_name,
            }

    async def _render_dispatch(self, task_prompt: str, prompt: str,
                               parsed_params: Optional[Dict[str, Any]] = None,
                               reference_image_base64: Optional[str] = None,
                               reference_mime: str = "image/png",
                               provider: Optional[str] = None,
                               reference_images: Optional[list] = None) -> Dict[str, Any]:
        """Elige el motor de render. Por defecto GEMINI, que es la IA 1.

        OJO, ESTE TEXTO ESTUVO MINTIENDO. Decía «por defecto MANUS (preferencia
        del usuario)», que fue verdad hasta que se apagó la IA 2 el 18/08/2026 y
        el defecto pasó a ser Gemini. El código estaba bien; la frase que lo
        describe, no — y el lío del 03/08 empezó exactamente así, con alguien
        creyéndose lo que ponía. Se corrigió al auditar, el 25/08/2026.

        Mapa vigente (CLAUDE.md, regla 1):

            IA 1 -> gemini           el de producción, y el único que ve un
                                     usuario que no sea master
            IA 3 -> gemini_premium   (flux si hay clave de Replicate)
            IA 7 -> julio11_plus     IA0 + geometría/vanos y entrada de mayor detalle
            IA 2 -> manus            APAGADA (MOTOR_MANUS_ACTIVO)
            IA 4 -> gemini_flash     APAGADA (era el mismo modelo que la IA 1)

        `provider` (el motor elegido en pantalla) manda sobre la variable de
        entorno KITCHEN_RENDER_PROVIDER. Quién puede pedir cada motor se decide
        ANTES de llegar aquí, en `routes/ai_engine.motor_permitido`: a quien no
        es master se le rebaja a la IA 1 aunque pida otra cosa por API.
        """
        import os
        # Gemini por defecto (mucho más fiel al croquis/referencia y devuelve la
        # imagen incrustada). Manus solo si se pide expresamente (IA 2) o por env.
        provider = (provider or os.environ.get("KITCHEN_RENDER_PROVIDER") or "gemini").lower()
        # IA 2 (Manus) ESTÁ APAGADA.
        #
        # El master, 18/08: «a la IA 2, cada vez que le mando hacer algo tarda un
        # montón» y luego «vamos a ir apagando lo que no estamos usando, apaga
        # la IA 2».
        #
        # Y tardaba por lo que es: Manus NO es un modelo de imagen, es un
        # AGENTE. Gemini es una llamada —le mandas el encargo y devuelve la
        # foto en unos segundos—; Manus crea una tarea, un agente se pone a
        # trabajar, y aquí se pregunta cada 5 segundos hasta 5 MINUTOS
        # (`wait_for_completion(timeout=300)`). Que tarde no era una avería.
        #
        # Lo que sí era nuestro es lo que costaba cuando NO salía: se agotaban
        # los 300 s y solo entonces se caía a Gemini. Cinco minutos de espera
        # para acabar con el render que Gemini habría dado al principio.
        #
        # APAGADA, NO BORRADA. El motor entero sigue aquí; lo único que hace
        # falta para volver a encenderlo es poner MOTOR_MANUS_ACTIVO=1 en el
        # entorno. Borrar una integración que costó escribir, para tener que
        # rehacerla si algún día se quiere, es tirar trabajo.
        _manus_encendido = os.environ.get("MOTOR_MANUS_ACTIVO", "").strip().lower() in (
            "1", "si", "sí", "true", "on")
        manus_ready = _manus_encendido and bool(getattr(self.config, "provider_api_key", ""))
        if provider == "manus" and not manus_ready:
            # Ni una palabra en silencio: si algo sigue pidiendo IA 2 —una
            # pestaña vieja abierta, una llamada guardada— queda dicho, y el
            # render sale igual por Gemini EN EL ACTO, sin los cinco minutos.
            logger.info(
                "Se ha pedido el motor IA 2 (Manus), que está apagado "
                "(MOTOR_MANUS_ACTIVO). Se rinde con el motor de siempre.")

        # IA7 mejorada usa el mismo perfil visual que IA0; solo cambian el
        # encargo estructural y la calidad de la referencia preparada antes.
        if provider == "julio11_plus":
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64,
                reference_mime=reference_mime,
                reference_images=reference_images,
                model_override="gemini-3-pro-image-preview",
            )

        # IA 0: modelo de imagen que estaba primero el 11/07/2026. Este camino
        # se mantiene explícito y separado para que IA1 siga usando su cascada
        # actual sin cambiar por una prueba histórica.
        if provider == "julio11":
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64,
                reference_mime=reference_mime,
                reference_images=reference_images,
                model_override="gemini-3-pro-image-preview",
            )

        # IA 2: Manus
        if provider == "manus" and manus_ready:
            res = await self._render_with_manus(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
            )
            if res.get("success"):
                return res
            logger.warning("Render con Manus falló; usando Gemini como respaldo.")

        # IA 3: Flux Pro (Replicate) si hay clave, si no cae a Gemini premium
        if provider == "flux":
            replicate_key = os.environ.get("REPLICATE_API_TOKEN", "").strip()
            if replicate_key:
                res = await self._render_with_flux(
                    task_prompt, prompt, parsed_params,
                    reference_image_base64=reference_image_base64, reference_mime=reference_mime,
                    replicate_key=replicate_key,
                )
                if res.get("success"):
                    return res
                logger.warning("Render con Flux falló; usando Gemini premium como respaldo.")
            else:
                logger.info("REPLICATE_API_TOKEN no configurado; usando Gemini premium para IA 3.")
            # Fallback a Gemini con prompt premium
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
                reference_images=reference_images,
                prompt_prefix=_PREMIUM_PROMPT_PREFIX,
            )

        # Perfil legado de prueba de modelo, conservado para compatibilidad.
        #
        # El master: «ponlo en la IA 7 con banana pro». Viene de preguntar en
        # qué se diferencia el ERP de abrir AI Studio y darle el dibujo a mano.
        # Se diferencia en el modelo: el ERP renderiza con `gemini-2.5-flash-
        # image` —Nano Banana normal— y AI Studio con Pro va con otro modelo,
        # mejor en detalle fino y en obedecer instrucciones largas.
        #
        # En `llm_vision` está escrita la decisión de NO usarlo: «gemini-3-pro-
        # image es más creativo e ignora el layout: se inventa la distribución
        # del cliente». Puede ser verdad, pero es una frase en un comentario y
        # no tiene ni una prueba detrás. Este botón la pone a prueba: MISMO
        # encargo que IA 1 —recorte, lectura a ficha y lista numerada— y solo
        # cambia el modelo. Si lo único que cambia es el modelo, lo que se ve
        # en las dos imágenes es el modelo.
        #
        # No se pone de motor por defecto: cuesta 0,12 $ por imagen frente a
        # 0,036 $, tres veces y pico. Que se elija a sabiendas.
        if provider == "banana_pro":
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
                reference_images=reference_images,
                model_override="gemini-3-pro-image-preview",
            )

        # IA 4: Gemini Flash (más rápido)
        if provider == "gemini_flash":
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
                reference_images=reference_images,
                model_override="gemini-2.5-flash-image",
            )

        # gemini_premium (legacy): Gemini con prompt enriquecido
        if provider == "gemini_premium":
            return await self._render_with_gemini(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
                reference_images=reference_images,
                prompt_prefix=_PREMIUM_PROMPT_PREFIX,
            )

        # IA 1 / default: Gemini estándar
        return await self._render_with_gemini(
            task_prompt, prompt, parsed_params,
            reference_image_base64=reference_image_base64, reference_mime=reference_mime,
            reference_images=reference_images,
        )

    def get_materials_catalog(self) -> Dict[str, Any]:
        """Devuelve el catálogo completo de materiales disponibles."""
        return {
            "countertops": COUNTERTOP_MATERIALS,
            "cabinets": CABINET_MATERIALS,
            "handles": HANDLE_STYLES,
            "floors": FLOOR_MATERIALS,
            "lighting": LIGHTING_STYLES,
            "layouts": [e.value for e in KitchenLayout],
            "styles": [e.value for e in RenderStyle],
            "engine": self.config.brand_name,
        }


# Singleton
_render_service: Optional[Render3DService] = None


def get_render_service() -> Render3DService:
    """Obtiene la instancia del servicio de render (singleton)."""
    global _render_service
    if _render_service is None:
        _render_service = Render3DService()
    return _render_service
