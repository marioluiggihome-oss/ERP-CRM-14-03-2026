# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""EL RENDER TAL Y COMO ERA EL 10 DE JULIO DE 2026. IA 5.

El master, mirando cuatro renders seguidos de la misma cocina: «busca lo que
hacía el 10 de julio de 2026, que funcionaba mejor». Y luego: «podías poner un
botón de IA 5, con el prompt del 10 de julio».

Tiene razón en el método. Llevábamos trece rondas de yo apretando el encargo y
él diciendo que no se parece. Un botón que rinda el MISMO croquis por los dos
caminos zanja la discusión en una prueba en vez de en una teoría.

QUÉ ES ESTO EXACTAMENTE
-----------------------
El camino del croquis del commit cbdd742 (10/07/2026, 22:55). No es «parecido»
ni «inspirado en»: las tres piezas —los principios de cocina, el constructor
de prompt y la nota del croquis— están sacadas LITERALMENTE de ese commit, sin
tocar una coma. Si se reescriben «mejorándolas», el botón deja de medir lo que
tiene que medir y la comparación no vale nada.

El motor es el mismo de entonces y el de hoy: Gemini. Lo único que cambia
entre IA 1 e IA 5 es el ENCARGO.

UNA CORRECCIÓN QUE ME DEBO
--------------------------
Le dije al master que el prompt de julio eran 164 palabras contra las 2.262 de
hoy, «casi catorce veces más». Era falso y decidió con ese número. Medí solo
la nota del croquis y me dejé fuera el andamiaje de `build_render_prompt`
—1.146 palabras más— y que el croquis pasaba además por `_expand_brief`, que
le pide a un LLM que REDACTE una especificación entera sin haber visto el
dibujo, y eso se sumaba encima.

El total real de julio son 1.310 palabras fijas MÁS lo que escribiera el LLM.
O sea que julio no era un prompt corto: era un prompt DISTINTO. Lo que
funcionaba mejor —si funcionaba mejor— no era la brevedad. Por eso el botón,
que mide, en vez de otra teoría mía.

LO QUE ESTE CAMINO NO LLEVA, PORQUE EN JULIO NO EXISTÍA
--------------------------------------------------------
Ni recorte del dibujo dentro de la página, ni lectura a ficha, ni la lista de
módulos numerada. Va el pantallazo tal cual, como iba entonces. Es a propósito:
un botón «julio con los arreglos de agosto» no contestaría a la pregunta.
"""
from __future__ import annotations

from typing import Optional


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


def build_render_prompt(
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
    if is_kitchen:
        parts.append(PRO_KITCHEN_DESIGN_PRINCIPLES)
    return " ".join(p for p in parts if p)


def prompt_del_croquis_10jul(prompt_generico: str, hay_referencia: bool = True,
                             es_croquis: bool = True) -> str:
    """El `task_prompt` del 10/07/2026, montado igual que aquel dia.

    `prompt_generico` es lo que devolvia `build_render_prompt` con el brief ya
    expandido, que es como llegaba entonces. Los nombres de dentro se
    conservan (`ref_b64`, `is_sketch`, `prompt`) para que el bloque siga siendo
    IDENTICO al del commit y se pueda contrastar linea a linea.
    """
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
    return task_prompt
