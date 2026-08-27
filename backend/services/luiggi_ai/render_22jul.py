# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""EL RENDER TAL Y COMO ERA EL 22 DE JULIO DE 2026. IA 5.

El master: «podemos poner en IA 5 lo que hacía el programa el 22 de julio, y
cómo interpretabas los dibujos». Antes este botón llevaba el camino del 10 de
julio, también suyo. El 22 es mejor, y se ve al ponerlos uno al lado del otro:

  10/07  «reproduce la distribución exacta: forma, número y orden de módulos,
          posición de cada electrodoméstico y las columnas».

  22/07  lo mismo Y ADEMÁS:
          · MODO ESTRUCTURA ESTRICTA / PRECISO, y el dibujo es «ground truth
            for GEOMETRY, not decoration»;
          · LOS VANOS: cada ventana y cada puerta en la MISMA posición, ancho y
            alto que en el dibujo. Esto no estaba el día 10 y es lo que hace
            que una cocina con una ventana sobre el fregadero salga con la
            ventana donde va;
          · los anchos de módulo A ESCALA del dibujo;
          · y la frase que lo cierra todo: «del texto SOLO salen acabados,
            materiales y colores; la geometría viene 100% del dibujo».

Esa última frase es la abuela de la regla que hoy sigue en el camino de
agosto. O sea que el 22 de julio no es un experimento raro: es de donde salió
lo que vino después.

QUÉ ES ESTO EXACTAMENTE
-----------------------
El camino del croquis del commit 8a48da5 (22/07/2026, 22:39). Las tres piezas
—los principios de cocina, el constructor de prompt y la nota del croquis—
están sacadas LITERALMENTE de ese commit, extraídas del repositorio y no
copiadas a mano. Si se reescriben «mejorándolas», el botón deja de medir lo
que tiene que medir.

Entre el 10 y el 22 solo cambió la NOTA DEL CROQUIS: `build_render_prompt`,
`_expand_brief` y los principios de cocina son idénticos en los dos días.
Comprobado antes de cambiar nada, no supuesto.

El motor es el mismo de entonces y el de hoy: Gemini. Lo único que cambia
entre IA 1 e IA 5 es el ENCARGO.

LO QUE NO LLEVA, PORQUE EN JULIO NO EXISTÍA
-------------------------------------------
Ni recorte del dibujo dentro de la página, ni lectura a ficha, ni lista de
módulos numerada, ni ancho total como ancla. Va el pantallazo tal cual, como
iba entonces. Es a propósito: un botón «julio con los arreglos de agosto» no
contestaría a la pregunta.
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


def prompt_del_croquis_22jul(prompt_generico: str, hay_referencia: bool = True,
                             es_croquis: bool = True) -> str:
    """El `task_prompt` del 22/07/2026, montado igual que aquel dia.

    `prompt_generico` es lo que devolvia `build_render_prompt` con el brief ya
    expandido, que es como llegaba entonces. Los nombres de dentro se conservan
    (`ref_b64`, `is_sketch`, `prompt`) para que el bloque siga siendo IDENTICO
    al del commit y se pueda contrastar linea a linea.
    """
    ref_b64 = hay_referencia
    is_sketch = es_croquis
    prompt = prompt_generico
    if ref_b64 and is_sketch:
        ref_note = (
            "A TECHNICAL 2D DRAWING (hand-drawn floor plan, elevation or blueprint) "
            "has been attached. Treat it in STRICT STRUCTURE / PRECISE MODE: it is "
            "the ground truth for GEOMETRY, not decoration. You MUST reproduce the "
            "EXACT distribution drawn: the SHAPE (linear, L-shaped, U-shaped), the "
            "NUMBER and ORDER of modules from left to right, the POSITION of each "
            "appliance (sink, dishwasher, washing machine, oven, hob, fridge), the "
            "TALL COLUMNS, and — critically — the OPENINGS: every window and door "
            "(vano) must appear at the SAME position, width and height as in the "
            "drawing, and the overall PROPORTIONS and module widths must match the "
            "drawing to scale. Do NOT add, remove, resize or rearrange any module or "
            "opening. Only the FINISHES, MATERIALS and COLORS come from the written "
            "brief; the geometry comes 100% from the drawing. "
        )
    elif ref_b64:
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
    return task_prompt
