# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""EL RENDER TAL Y COMO ERA EL 11 DE JULIO DE 2026.

Este módulo es una pieza de comparación histórica. No debe incorporar las reglas
posteriores de agosto (recorte de página, lectura a ficha, lista numerada de
módulos o anclaje por ancho total), porque entonces IA0 dejaría de medir el
camino que funcionaba el 11/07/2026.

El constructor genérico se comparte con el módulo histórico de julio porque el
historial del proyecto documenta que `build_render_prompt`, la expansión del
brief y los principios profesionales de cocina eran iguales entre el 10 y el
22 de julio. Solo se congela aquí la nota de croquis del 11/07.
"""
from __future__ import annotations

from .render_22jul import build_render_prompt


def prompt_del_croquis_11jul(
    prompt_generico: str,
    hay_referencia: bool = True,
    es_croquis: bool = True,
) -> str:
    """Monta el prompt literal del camino de generación del 11/07/2026."""
    ref_b64 = hay_referencia
    is_sketch = es_croquis
    prompt = prompt_generico

    if ref_b64 and is_sketch:
        ref_note = (
            "A HAND-DRAWN FLOOR PLAN / SKETCH has been attached. It shows the "
            "exact kitchen/furniture LAYOUT drawn by the designer. You MUST "
            "reproduce the EXACT distribution shown in the sketch: the SHAPE "
            "(linear, L-shaped, U-shaped), the NUMBER and ORDER of modules from "
            "left to right, the POSITION of each appliance (sink, dishwasher, "
            "washing machine, oven, hob, fridge), and the TALL COLUMNS. "
            "The sketch is NOT decorative — it is a TECHNICAL blueprint. "
            "Generate the kitchen EXACTLY as drawn, with the materials and "
            "colors described in the brief below. Do NOT add, remove, or "
            "rearrange any module. The proportions and widths of each module "
            "must match the sketch. "
        )
    elif ref_b64:
        ref_note = (
            "An IMAGE has been attached as visual reference (a photo, a sketch or a "
            "technical breakdown/despiece). Use it to respect the real LAYOUT, "
            "PROPORTIONS and MEASUREMENTS of the piece (number and size of doors, "
            "drawers, shelves and columns). Keep the geometry faithful to the "
            "reference; apply the finishes/colors from the brief. "
        )
    else:
        ref_note = ""

    return (
        "Generate a single high-quality, photorealistic 3D render image based "
        "STRICTLY on the following design brief. Reproduce exactly what is "
        "described (type of furniture or space, exterior doors, finishes, "
        "colors, handles/pulls, materials and interior layout such as shelves, "
        "columns or drawers). Do NOT default to a kitchen unless the brief "
        "explicitly asks for one. "
        + ref_note
        + "\n\n"
        + prompt
        + "\n\n"
        "The result must look like a real professional interior photograph "
        "(photorealistic, PBR materials, natural light, realistic shadows and "
        "reflections), NOT a cartoon or videogame-style 3D image. Avoid plastic, "
        "flat or oversaturated looks. No text, watermarks, or logos in the image."
    )
