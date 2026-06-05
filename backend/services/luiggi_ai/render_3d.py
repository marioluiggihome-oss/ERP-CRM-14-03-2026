"""
LuiggiAI Engine - Servicio de Render 3D
========================================
Genera renders fotorrealistas de cocinas y espacios interiores
a partir de descripciones en texto natural o voz transcrita.

Integra el skill de kitchen-3d-render para construir prompts
optimizados que producen resultados de alta calidad.
"""

import logging
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

        # Estilo de renderizado
        style_instructions = {
            "photorealistic": "Ultra-photorealistic 3D render, 8K resolution, ray-traced lighting, subtle depth of field",
            "architectural": "Professional architectural visualization, clean lines, accurate proportions, neutral lighting",
            "magazine": "Interior design magazine cover quality, styled with accessories, warm inviting atmosphere",
            "minimalist": "Clean minimalist aesthetic, uncluttered surfaces, zen-like simplicity, soft shadows",
            "warm": "Warm cozy atmosphere, golden hour lighting, lived-in feeling with subtle styling",
            "industrial": "Industrial loft style, exposed elements, raw materials, dramatic contrast lighting",
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
            "Camera angle: eye-level perspective showing the full kitchen layout.",
            "The space should feel realistic, livable, and professionally designed.",
            "No text, watermarks, or logos in the image.",
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

    async def generate_render(
        self,
        description: str,
        params_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Genera un render 3D a partir de una descripción (texto o voz transcrita).

        Args:
            description: Descripción en lenguaje natural
            params_override: Parámetros explícitos que sobreescriben el parsing

        Returns:
            Dict con el resultado del render
        """
        # Parsear descripción natural
        parsed_params = self.parse_natural_language(description)

        # Aplicar overrides si los hay
        if params_override:
            parsed_params.update(params_override)

        # Construir prompt optimizado
        prompt = self.build_kitchen_prompt(
            layout=parsed_params.get("layout", "L-shape"),
            countertop=parsed_params.get("countertop", "quartz_white"),
            cabinets=parsed_params.get("cabinets", "white_matte"),
            handles=parsed_params.get("handles", "bar_black"),
            floor=parsed_params.get("floor", "wood_oak"),
            lighting=parsed_params.get("lighting", "natural"),
            style=parsed_params.get("style", "photorealistic"),
            additional_details=parsed_params.get("additional_details"),
        )

        # Crear tarea de generación de imagen
        task_prompt = (
            f"Generate a high-quality 3D render image based on this description:\n\n"
            f"{prompt}\n\n"
            f"Output: A single photorealistic image of the kitchen design. "
            f"The image should look like a professional interior design visualization."
        )

        result = await self.engine.create_task(prompt=task_prompt)

        if result.get("success"):
            task_id = result["task_id"]
            # Esperar resultado (render puede tardar)
            final = await self.engine.wait_for_completion(task_id, timeout=180)
            final["parsed_params"] = parsed_params
            final["prompt_used"] = prompt
            return final

        return result

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
            f"Generate a high-quality 3D render image:\n\n{prompt}\n\n"
            f"Output: A single photorealistic interior design visualization image."
        )

        result = await self.engine.create_task(prompt=task_prompt)

        if result.get("success"):
            task_id = result["task_id"]
            final = await self.engine.wait_for_completion(task_id, timeout=180)
            final["prompt_used"] = prompt
            return final

        return result

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
