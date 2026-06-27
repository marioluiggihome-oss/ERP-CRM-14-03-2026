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
        kitchen_scale = (
            "Use real kitchen cabinetry scale: base units ~90 cm high with a recessed toe-kick "
            "plinth, wall units mounted ~55-60 cm above a continuous worktop of uniform thickness "
            "with a matching upstand/backsplash, and appliances integrated flush with the fronts; "
            "keep reveal gaps between fronts uniform. "
            if is_kitchen else ""
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
        return " ".join(parts)

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

        # Detectar el tipo de espacio/mueble para NO forzar "cocina"
        space_type = self.detect_space_type(description)
        parsed_params["space_type"] = space_type

        # Preparar la imagen de referencia (si es PDF, convertir 1ª página a PNG)
        ref_b64, ref_mime = self._prepare_reference(reference_image, reference_mime)
        parsed_params["hasReference"] = bool(ref_b64)

        # Expandir el brief con un LLM potente (gemini-2.5-pro) para que las órdenes
        # sean mucho más explícitas y el render obedezca con detalle.
        expanded_brief = await self._expand_brief(description, space_type)
        parsed_params["briefExpanded"] = bool(expanded_brief) and expanded_brief != (description or "").strip()

        # Construir prompt GENÉRICO guiado por la descripción (ya expandida).
        prompt = self.build_render_prompt(
            description=expanded_brief or description,
            style=parsed_params.get("style", "photorealistic"),
            space_type=space_type,
        )

        # Crear tarea de generación de imagen (genérica, dirigida por el brief)
        ref_note = (
            "An IMAGE has been attached as visual reference (a photo, a sketch or a "
            "technical breakdown/despiece). Use it to respect the real LAYOUT, "
            "PROPORTIONS and MEASUREMENTS of the piece (number and size of doors, "
            "drawers, shelves and columns). Keep the geometry faithful to the "
            "reference; apply the finishes/colors from the brief. "
            if ref_b64 else ""
        )
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
        )

    async def generate_render_composed(
        self,
        description: str,
        floor_plan: Optional[str] = None,
        wall_sketches: Optional[list] = None,
        params_override: Optional[Dict[str, Any]] = None,
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
        space_type = self.detect_space_type(description or "cocina")
        parsed_params["space_type"] = space_type

        images = []       # [{"data","mime"}] para la generación multi-imagen
        ref_lines = []    # descripción textual de cada imagen para el prompt

        if floor_plan:
            b64, mime = self._prepare_reference(floor_plan, None)
            if b64:
                images.append({"data": b64, "mime": mime})
                ref_lines.append(
                    f"- IMAGE {len(images)} is the FLOOR PLAN (top-down view): it defines the "
                    "exact LAYOUT — position and length of every wall, placement of cabinets/"
                    "furniture, doors and windows. Respect these positions and proportions."
                )

        for i, sk in enumerate(wall_sketches or []):
            b64, mime = self._prepare_reference(sk, None)
            if b64:
                images.append({"data": b64, "mime": mime})
                ref_lines.append(
                    f"- IMAGE {len(images)} is a SKETCH of WALL {i + 1}: it shows the desired "
                    "design of that wall (cabinets, shelves, appliances, finishes, proportions). "
                    "Reproduce that wall faithfully."
                )

        if not images:
            return {
                "success": False,
                "status": "failed",
                "error": "Adjunta al menos el plano en planta o un boceto de pared.",
                "engine": self.config.brand_name,
            }

        expanded_brief = await self._expand_brief(description, space_type)
        prompt = self.build_render_prompt(
            description=expanded_brief or description,
            style=parsed_params.get("style", "photorealistic"),
            space_type=space_type,
        )
        refs_block = "\n".join(ref_lines)
        task_prompt = (
            "You are a professional architectural visualizer. You are given MULTIPLE reference "
            "images that you must COMBINE into ONE single photorealistic interior render:\n"
            + refs_block + "\n\n"
            "TREAT THE REFERENCES AS AUTHORITATIVE GEOMETRY. The floor plan defines the exact "
            "room shape, wall lengths and the position/length of every cabinet run, island, "
            "door and window — keep these positions, alignments and proportions to scale. Each "
            "wall sketch defines the exact elevation of that wall: reproduce the SAME number, "
            "order, width and height of modules (base units, wall units, tall columns, drawers, "
            "open shelves and appliances) shown there. Count the fronts in each sketch and match "
            "them exactly — do not add, remove, merge or reorder modules.\n\n"
            "Produce a single ultra-photorealistic photograph of the FINISHED space that is "
            "FAITHFUL at the same time to the floor-plan layout and to EACH wall sketch, "
            "applying the finishes, colors and materials described in the brief. If this is a "
            "kitchen, use real cabinetry scale: base units ~90 cm with a recessed toe-kick, "
            "wall units ~55-60 cm above a continuous worktop of uniform thickness with a "
            "matching upstand, and appliances integrated flush with the fronts. Do NOT invent "
            "extra walls, appliances, furniture, decorative objects or architectural elements "
            "(windows, doors, columns…) that do not appear in the reference images or the brief, "
            "and do NOT omit any element that DOES appear in them. If a reference is unclear "
            "about a detail, keep that area plain and neutral instead of guessing.\n\n"
            f"{prompt}\n\n"
            "The result must look like a real professional interior photograph: PBR materials "
            "with accurate roughness and reflectivity, natural directional daylight, realistic "
            "soft shadows, ambient occlusion and subtle reflections, neutral white balance and "
            "true-to-scale proportions. Negative — strictly avoid: cartoon/CGI/videogame look, "
            "plastic or flat surfaces, oversaturated colors, warped or melted geometry, crooked "
            "or duplicated modules, floating cabinets, invented decor, people, text, watermarks "
            "and logos."
        )
        parsed_params["hasReference"] = True
        parsed_params["referenceCount"] = len(images)
        return await self._render_with_gemini(
            task_prompt, prompt, parsed_params, reference_images=images,
        )

    def _prepare_reference(self, reference_image, reference_mime):
        """Normaliza la referencia: quita el prefijo data:, y si es PDF convierte
        la primera página a PNG para que el modelo de imagen la pueda usar."""
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
                pages = pdf_base64_to_png_base64(raw, dpi=150, max_pages=1) or []
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
                                  reference_images: Optional[list] = None) -> Dict[str, Any]:
        """Genera el render con Gemini y lo devuelve como data URL (marca blanca)."""
        from services.llm_vision import generate_image_with_gemini
        start = time.time()
        try:
            data_url = await generate_image_with_gemini(
                task_prompt,
                reference_image_base64=reference_image_base64,
                reference_mime=reference_mime or "image/png",
                reference_images=reference_images,
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
            out["parsed_params"] = parsed_params
        return out

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
                               reference_mime: str = "image/png") -> Dict[str, Any]:
        """Elige el motor de render. Por defecto MANUS (preferencia del usuario);
        si no está configurado o falla, usa Gemini como respaldo.
        Configurable con la variable de entorno KITCHEN_RENDER_PROVIDER=manus|gemini."""
        import os
        provider = (os.environ.get("KITCHEN_RENDER_PROVIDER") or "manus").lower()
        manus_ready = bool(getattr(self.config, "provider_api_key", ""))

        if provider == "manus" and manus_ready:
            res = await self._render_with_manus(
                task_prompt, prompt, parsed_params,
                reference_image_base64=reference_image_base64, reference_mime=reference_mime,
            )
            if res.get("success"):
                return res
            logger.warning("Render con Manus falló; usando Gemini como respaldo.")

        return await self._render_with_gemini(
            task_prompt, prompt, parsed_params,
            reference_image_base64=reference_image_base64, reference_mime=reference_mime,
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
